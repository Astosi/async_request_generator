def boxify(header, params):
    lines = []

    max_key_width = max(len(header), max(len(str(key)) for key in params.keys()))
    max_value_width = max(len(str(key)) for key in params.values())
    width = max_key_width + max_value_width

    # Add headline
    lines.append(f"\n\t+{'-' * (width + 4)}+")
    lines.append(f"| \033[1;36;10m{header:^{width + 2}}\033[0m |")
    lines.append(f"+{'-' * (width + 4)}+")

    # Add parameters
    for key, value in params.items():
        lines.append(f"| \033[1;38;10m{key :<{max_key_width}}\033[0m : \033[1;31;10m{str(value):<{max_value_width}}\033[0m|")
    lines.append(f"+{'-' * (width+4)}+")

    box = "\n\t".join(lines)
    return box
