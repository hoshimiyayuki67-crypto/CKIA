import argparse
from pathlib import Path

from campus_assistant.repositories.knowledge import KnowledgeRepository


def main():
    parser = argparse.ArgumentParser(description="校验人工结构化知识记录，不会自动批准资料")
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    if not args.directory.is_dir():
        parser.error("知识目录不存在")
    repository = KnowledgeRepository.load(args.directory)
    print(f"有效结构记录: {len(repository.entries)}")
    print(f"标记已审核: {sum(entry.reviewed for entry in repository.entries)}")


if __name__ == "__main__":
    main()
