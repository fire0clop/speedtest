#!/usr/bin/env python3
"""Замер скорости скачивания: N последовательных запросов к одному адресу."""

import argparse
import ssl
import sys
import time
import urllib.request

CHUNK_SIZE = 64 * 1024  # читаем ответ кусками по 64 КБ, чтобы не держать всё в памяти


def make_ssl_context() -> ssl.SSLContext:
    """Python с python.org на macOS не видит системные сертификаты.
    Если установлен certifi — берём сертификаты из него, иначе системные."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


SSL_CONTEXT = make_ssl_context()


def download(url: str, timeout: float) -> tuple[int, float]:
    """Скачивает url целиком. Возвращает (сколько байт получено, сколько секунд заняло)."""
    request = urllib.request.Request(url, headers={"User-Agent": "speedtest-script/1.0"})
    start = time.perf_counter()
    total_bytes = 0
    with urllib.request.urlopen(request, timeout=timeout, context=SSL_CONTEXT) as response:
        while chunk := response.read(CHUNK_SIZE):
            total_bytes += len(chunk)
    elapsed = time.perf_counter() - start
    return total_bytes, elapsed


def main() -> int:
    parser = argparse.ArgumentParser(description="Замер скорости скачивания по URL.")
    parser.add_argument("url", help="адрес, к которому делать запросы")
    parser.add_argument("-n", "--requests", type=int, default=10, help="число запросов (по умолчанию 10)")
    parser.add_argument("-t", "--timeout", type=float, default=30, help="таймаут одного запроса, сек")
    args = parser.parse_args()

    if args.requests < 1:
        parser.error("число запросов должно быть >= 1")

    total_bytes = 0
    total_time = 0.0

    for i in range(1, args.requests + 1):
        try:
            size, elapsed = download(args.url, args.timeout)
        except Exception as error:  # сеть, HTTP-ошибка, таймаут, кривой URL
            print(f"Запрос {i}: ошибка — {error}", file=sys.stderr)
            return 1
        total_bytes += size
        total_time += elapsed
        print(f"Запрос {i:>2}: {size / 1_000_000:8.2f} МБ за {elapsed:6.3f} с")

    avg_time = total_time / args.requests
    # Скорость = все скачанные биты / всё время скачивания. 1 Мбит = 1 000 000 бит.
    speed_mbit = total_bytes * 8 / total_time / 1_000_000 if total_time > 0 else 0.0

    print()
    print(f"Среднее время запроса: {avg_time:.3f} с")
    print(f"Всего скачано:         {total_bytes / 1_000_000:.2f} МБ ({total_bytes} байт)")
    print(f"Скорость скачивания:   {speed_mbit:.2f} Мбит/с")
    return 0


if __name__ == "__main__":
    sys.exit(main())
