from __future__ import annotations

import argparse
import json
from pathlib import Path


SPLITS = ("train", "test", "shifted_test")


def task_id(split: str, name: str) -> str:
    return f"expanded_{split}_{name}"


def build_tasks() -> list[dict[str, object]]:
    patterns = [
        {
            "name": "sum_even",
            "description": "Return the sum of all even integers in the input list.",
            "buggy": "def FUNC(nums):\n    total = 0\n    for n in nums:\n        if n % 2 == 1:\n            total += n\n    return total\n",
            "solution": "def FUNC(nums):\n    total = 0\n    for n in nums:\n        if n % 2 == 0:\n            total += n\n    return total\n",
            "tests": [["assert FUNC([1, 2, 3, 4]) == 6"], ["assert FUNC([-2, -1, 0, 3]) == -2"], ["assert FUNC([]) == 0", "assert FUNC([2, 2, 2]) == 6"]],
        },
        {
            "name": "safe_max",
            "description": "Return the maximum value, or None when the input list is empty.",
            "buggy": "def FUNC(nums):\n    best = 0\n    for n in nums:\n        if n > best:\n            best = n\n    return best\n",
            "solution": "def FUNC(nums):\n    if not nums:\n        return None\n    best = nums[0]\n    for n in nums[1:]:\n        if n > best:\n            best = n\n    return best\n",
            "tests": [["assert FUNC([3, 1, 9]) == 9", "assert FUNC([]) is None"], ["assert FUNC([-5, -2, -8]) == -2"], ["assert FUNC([]) is None", "assert FUNC([0]) == 0"]],
        },
        {
            "name": "palindrome",
            "description": "Return True only when the string is a palindrome ignoring case.",
            "buggy": "def FUNC(text):\n    return text == text[::-1]\n",
            "solution": "def FUNC(text):\n    normalized = text.lower()\n    return normalized == normalized[::-1]\n",
            "tests": [["assert FUNC('RaceCar') is True"], ["assert FUNC('Python') is False", "assert FUNC('Level') is True"], ["assert FUNC('') is True", "assert FUNC('A') is True", "assert FUNC('NoOn') is True"]],
        },
        {
            "name": "flatten_once",
            "description": "Flatten exactly one level of nested lists while preserving scalar items.",
            "buggy": "def FUNC(items):\n    result = []\n    for item in items:\n        result.append(item)\n    return result\n",
            "solution": "def FUNC(items):\n    result = []\n    for item in items:\n        if isinstance(item, list):\n            result.extend(item)\n        else:\n            result.append(item)\n    return result\n",
            "tests": [["assert FUNC([[1, 2], [3], 4]) == [1, 2, 3, 4]"], ["assert FUNC([1, [2, 3], 4]) == [1, 2, 3, 4]"], ["assert FUNC([]) == []", "assert FUNC([[1, [2]]]) == [1, [2]]"]],
        },
        {
            "name": "word_counts",
            "description": "Count words by splitting the input text on whitespace.",
            "buggy": "def FUNC(text):\n    counts = {}\n    for word in text.split(','):\n        counts[word] = counts.get(word, 0) + 1\n    return counts\n",
            "solution": "def FUNC(text):\n    counts = {}\n    for word in text.split():\n        counts[word] = counts.get(word, 0) + 1\n    return counts\n",
            "tests": [["assert FUNC('a b a') == {'a': 2, 'b': 1}"], ["assert FUNC('one two two') == {'one': 1, 'two': 2}"], ["assert FUNC('') == {}", "assert FUNC('a\\tb\\na') == {'a': 2, 'b': 1}"]],
        },
        {
            "name": "clamp",
            "description": "Clamp a number to the inclusive interval from low to high.",
            "buggy": "def FUNC(value, low, high):\n    return min(low, max(value, high))\n",
            "solution": "def FUNC(value, low, high):\n    return max(low, min(value, high))\n",
            "tests": [["assert FUNC(5, 0, 10) == 5"], ["assert FUNC(-3, 0, 10) == 0", "assert FUNC(5, 0, 10) == 5"], ["assert FUNC(99, 0, 10) == 10", "assert FUNC(4, 4, 4) == 4"]],
        },
        {
            "name": "factorial",
            "description": "Return the factorial of a non-negative integer.",
            "buggy": "def FUNC(n):\n    total = 1\n    for value in range(1, n):\n        total *= value\n    return total\n",
            "solution": "def FUNC(n):\n    total = 1\n    for value in range(2, n + 1):\n        total *= value\n    return total\n",
            "tests": [["assert FUNC(5) == 120"], ["assert FUNC(3) == 6"], ["assert FUNC(0) == 1", "assert FUNC(1) == 1", "assert FUNC(4) == 24"]],
        },
        {
            "name": "fizz_buzz",
            "description": "Return FizzBuzz labels from 1 through n, using FizzBuzz for multiples of fifteen.",
            "buggy": "def FUNC(n):\n    result = []\n    for value in range(1, n + 1):\n        if value % 3 == 0:\n            result.append('Fizz')\n        elif value % 5 == 0:\n            result.append('Buzz')\n        else:\n            result.append(str(value))\n    return result\n",
            "solution": "def FUNC(n):\n    result = []\n    for value in range(1, n + 1):\n        if value % 15 == 0:\n            result.append('FizzBuzz')\n        elif value % 3 == 0:\n            result.append('Fizz')\n        elif value % 5 == 0:\n            result.append('Buzz')\n        else:\n            result.append(str(value))\n    return result\n",
            "tests": [["assert FUNC(5) == ['1', '2', 'Fizz', '4', 'Buzz']", "assert FUNC(15)[-1] == 'FizzBuzz'"], ["assert FUNC(15)[-1] == 'FizzBuzz'"], ["assert FUNC(0) == []", "assert FUNC(3) == ['1', '2', 'Fizz']", "assert FUNC(15)[-1] == 'FizzBuzz'"]],
        },
        {
            "name": "dedupe_ordered",
            "description": "Remove duplicates while preserving the first-occurrence order.",
            "buggy": "def FUNC(items):\n    return sorted(set(items))\n",
            "solution": "def FUNC(items):\n    result = []\n    seen = set()\n    for item in items:\n        if item not in seen:\n            seen.add(item)\n            result.append(item)\n    return result\n",
            "tests": [["assert FUNC(['b', 'a', 'b', 'c']) == ['b', 'a', 'c']"], ["assert FUNC(['b', 'a', 'b', 'c']) == ['b', 'a', 'c']"], ["assert FUNC([]) == []", "assert FUNC([1, 1, 1]) == [1]", "assert FUNC(['b', 'a', 'b']) == ['b', 'a']"]],
        },
        {
            "name": "merge_counts",
            "description": "Merge two count dictionaries by adding values for shared keys.",
            "buggy": "def FUNC(first, second):\n    result = dict(first)\n    result.update(second)\n    return result\n",
            "solution": "def FUNC(first, second):\n    result = dict(first)\n    for key, value in second.items():\n        result[key] = result.get(key, 0) + value\n    return result\n",
            "tests": [["assert FUNC({'a': 2}, {'b': 1}) == {'a': 2, 'b': 1}", "assert FUNC({'a': 2}, {'a': 3}) == {'a': 5}"], ["assert FUNC({'a': 2}, {'a': 3}) == {'a': 5}"], ["assert FUNC({}, {'x': 1}) == {'x': 1}", "assert FUNC({'x': 1}, {}) == {'x': 1}", "assert FUNC({'x': 2}, {'x': 4}) == {'x': 6}"]],
        },
        {
            "name": "first_index",
            "description": "Return the index of the first matching value, or -1 if it is absent.",
            "buggy": "def FUNC(items, target):\n    for index, item in enumerate(items):\n        if item == target:\n            return index\n    return 0\n",
            "solution": "def FUNC(items, target):\n    for index, item in enumerate(items):\n        if item == target:\n            return index\n    return -1\n",
            "tests": [["assert FUNC([3, 4, 5], 4) == 1", "assert FUNC([3, 4, 5], 8) == -1"], ["assert FUNC([1, 2, 1], 1) == 0", "assert FUNC([1, 2], 9) == -1"], ["assert FUNC([], 2) == -1", "assert FUNC([1, 2], 9) == -1"]],
        },
        {
            "name": "average",
            "description": "Return the arithmetic mean, or None for an empty list.",
            "buggy": "def FUNC(numbers):\n    return sum(numbers) // len(numbers)\n",
            "solution": "def FUNC(numbers):\n    if not numbers:\n        return None\n    return sum(numbers) / len(numbers)\n",
            "tests": [["assert FUNC([2, 4, 6]) == 4", "assert FUNC([1, 2]) == 1.5"], ["assert FUNC([1, 2]) == 1.5"], ["assert FUNC([]) is None", "assert FUNC([-2, 2]) == 0"]],
        },
        {
            "name": "rotate_right",
            "description": "Rotate a list to the right by the requested number of steps.",
            "buggy": "def FUNC(items, steps):\n    if not items:\n        return []\n    steps = steps % len(items)\n    return items[steps:] + items[:steps]\n",
            "solution": "def FUNC(items, steps):\n    if not items:\n        return []\n    steps = steps % len(items)\n    return items[-steps:] + items[:-steps] if steps else list(items)\n",
            "tests": [["assert FUNC([1, 2, 3], 1) == [3, 1, 2]"], ["assert FUNC(['a', 'b', 'c', 'd'], 1) == ['d', 'a', 'b', 'c']"], ["assert FUNC([], 3) == []", "assert FUNC([1, 2], 4) == [1, 2]", "assert FUNC([1, 2, 3], 1) == [3, 1, 2]"]],
        },
        {
            "name": "count_vowels",
            "description": "Count vowels in a string regardless of letter case.",
            "buggy": "def FUNC(text):\n    return sum(char in 'aeiou' for char in text)\n",
            "solution": "def FUNC(text):\n    return sum(char in 'aeiou' for char in text.lower())\n",
            "tests": [["assert FUNC('hello') == 2", "assert FUNC('AEIOU') == 5"], ["assert FUNC('AEIOU') == 5"], ["assert FUNC('') == 0", "assert FUNC('PyThOn') == 1"]],
        },
        {
            "name": "normalize_spaces",
            "description": "Normalize whitespace by trimming and joining words with single spaces.",
            "buggy": "def FUNC(text):\n    return text.replace(' ', '')\n",
            "solution": "def FUNC(text):\n    return ' '.join(text.split())\n",
            "tests": [["assert FUNC('a  b') == 'a b'"], ["assert FUNC('  hello world  ') == 'hello world'"], ["assert FUNC('a\\tb\\nc') == 'a b c'", "assert FUNC('   ') == ''"]],
        },
    ]

    tasks: list[dict[str, object]] = []
    for pattern in patterns:
        for split_index, split in enumerate(SPLITS):
            function_name = f"{pattern['name']}_{split}"
            replace = lambda text: text.replace("FUNC", function_name)
            tasks.append(
                {
                    "task_id": task_id(split, str(pattern["name"])),
                    "split": split,
                    "task_family": "code_repair",
                    "difficulty": "medium" if split == "shifted_test" else "easy",
                    "description": str(pattern["description"]),
                    "buggy_code": replace(str(pattern["buggy"])),
                    "entry_point": function_name,
                    "tests": [replace(test) for test in pattern["tests"][split_index]],
                    "reference_solution": replace(str(pattern["solution"])),
                }
            )
    return tasks


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the expanded synthetic code-repair benchmark.")
    parser.add_argument("--output", default="data/tasks_code/expanded_code_repair.json")
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    tasks = build_tasks()
    with output.open("w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2)
        f.write("\n")
    counts = {split: sum(task["split"] == split for task in tasks) for split in SPLITS}
    print(json.dumps({"output": str(output), "num_tasks": len(tasks), "split_counts": counts}, indent=2))


if __name__ == "__main__":
    main()
