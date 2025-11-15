"""Utility to scrape answers from a Zhihu question link.

This script uses Zhihu's public API endpoints to fetch answers for a question,
converting them to plain text and optionally saving them to a file.
"""
from __future__ import annotations

import argparse
import re
import sys
import time
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Iterable, List, Optional

import requests


QUESTION_ID_PATTERN = re.compile(r"questions/(\d+)")


class ZhihuTextExtractor(HTMLParser):
    """Simplistic HTML -> text converter for Zhihu answer content."""

    def __init__(self) -> None:
        super().__init__()
        self._parts: List[str] = []
        self._needs_space = False

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[override]
        if tag in {"p", "div", "blockquote"}:
            self._append_newline()
        elif tag in {"br", "li"}:
            self._append_newline()
        elif tag == "code":
            self._append_newline()

    def handle_endtag(self, tag: str) -> None:  # type: ignore[override]
        if tag in {"p", "div", "blockquote", "li", "code"}:
            self._append_newline()

    def handle_data(self, data: str) -> None:  # type: ignore[override]
        text = data.strip()
        if not text:
            return
        if self._needs_space:
            self._parts.append(" ")
            self._needs_space = False
        self._parts.append(text)
        self._needs_space = True

    def handle_entityref(self, name: str) -> None:  # type: ignore[override]
        self.handle_data(self.unescape(f"&{name};"))

    def handle_charref(self, name: str) -> None:  # type: ignore[override]
        self.handle_data(self.unescape(f"&#{name};"))

    def _append_newline(self) -> None:
        if self._parts and self._parts[-1] != "\n":
            self._parts.append("\n")
            self._needs_space = False

    def get_text(self) -> str:
        text = "".join(self._parts)
        # Collapse multiple blank lines to at most two.
        return re.sub(r"\n{3,}", "\n\n", text).strip()


def html_to_text(html: str) -> str:
    parser = ZhihuTextExtractor()
    parser.feed(html)
    parser.close()
    return parser.get_text()


@dataclass
class Answer:
    id: str
    author: str
    created_time: int
    updated_time: int
    url: str
    text: str


class ZhihuScraper:
    API_TEMPLATE = (
        "https://www.zhihu.com/api/v4/questions/{question_id}/answers"
        "?include=data%5B*%5D.is_normal,admin_closed_comment,reward_info,is_collapsed,"
        "annotation_action,annotation_detail,collapse_reason,is_sticky,collapsed_by,"
        "suggest_edit,comment_count,can_comment,content,editable_content,voteup_count,"
        "reshipment_settings,comment_permission,created_time,updated_time,review_info,"
        "relevant_info,question,excerpt,relationship.is_authorized,is_author,voting,is_thanked,"
        "is_nothelp,is_labeled,author,fold_tip,ad_info,mark_infos,referenced_infos,"
        "reaction_instruction,relationship.is_public_edit"
        "&limit={limit}&offset={offset}"
    )

    def __init__(self, question_id: str, session: Optional[requests.Session] = None) -> None:
        self.question_id = question_id
        self.session = session or requests.Session()
        self.session.headers.setdefault(
            "User-Agent",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/118.0.0.0 Safari/537.36",
        )

    def fetch_answers(self, limit: int = 20, delay: float = 0.5) -> Iterable[Answer]:
        offset = 0
        while True:
            url = self.API_TEMPLATE.format(question_id=self.question_id, limit=limit, offset=offset)
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
            payload = response.json()
            data = payload.get("data", [])
            for item in data:
                yield Answer(
                    id=str(item.get("id")),
                    author=_extract_author_name(item.get("author")),
                    created_time=item.get("created_time", 0),
                    updated_time=item.get("updated_time", 0),
                    url=item.get("url", ""),
                    text=html_to_text(item.get("content", "")),
                )
            paging = payload.get("paging", {})
            if paging.get("is_end"):
                break
            offset += limit
            time.sleep(delay)


def _extract_author_name(author_info: Optional[dict]) -> str:
    if not author_info:
        return "匿名用户"
    name = author_info.get("name")
    if name:
        return name
    if author_info.get("type") == "people" and author_info.get("headline"):
        return author_info["headline"]
    return author_info.get("url_token", "匿名用户")


def parse_question_id(link: str) -> str:
    match = QUESTION_ID_PATTERN.search(link)
    if not match:
        raise ValueError(
            "无法从提供的链接中解析出问题 ID，请确保链接格式类似于 "
            "https://www.zhihu.com/question/123456789"
        )
    return match.group(1)


def format_answers(answers: Iterable[Answer]) -> str:
    output_lines: List[str] = []
    for idx, answer in enumerate(answers, start=1):
        output_lines.append(f"答案 {idx}（作者：{answer.author}）")
        output_lines.append("-" * 40)
        output_lines.append(answer.text or "（无文字内容）")
        output_lines.append("\n")
    return "\n".join(output_lines).strip()


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="抓取知乎问题下的所有回答")
    parser.add_argument("url", help="知乎问题的链接，例如：https://www.zhihu.com/question/123456")
    parser.add_argument(
        "--output",
        "-o",
        help="输出文件路径，不提供则打印到终端",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="每次请求抓取的回答数量，默认 20，最大建议不要超过 20",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="每次请求之间的延迟（秒），避免触发反爬机制，默认 0.5",
    )
    parser.add_argument(
        "--cookie",
        help="若需要登录凭证，请提供知乎 Cookie",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    try:
        question_id = parse_question_id(args.url)
    except ValueError as exc:  # pragma: no cover - simple CLI validation
        print(exc, file=sys.stderr)
        return 2

    session = requests.Session()
    if args.cookie:
        session.headers["Cookie"] = args.cookie

    scraper = ZhihuScraper(question_id, session=session)

    try:
        answers = list(scraper.fetch_answers(limit=args.limit, delay=args.delay))
    except requests.HTTPError as exc:  # pragma: no cover - depends on runtime
        print(f"请求知乎接口失败：{exc}", file=sys.stderr)
        return 3
    except requests.RequestException as exc:  # pragma: no cover - depends on runtime
        print(f"网络请求出现异常：{exc}", file=sys.stderr)
        return 4

    if not answers:
        print("未获取到任何回答。")
        return 0

    output_text = format_answers(answers)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_text)
        print(f"已将 {len(answers)} 条回答保存到 {args.output}")
    else:
        print(output_text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
