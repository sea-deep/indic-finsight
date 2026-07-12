try:
    args = "Reliance Industries annual report revenue breakdown by segment"
    arg_val = list(args.values())[0] if args else ""
except Exception as e:
    print(repr(e))
