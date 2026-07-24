import glob       # for fuzzy file name search

def depacketizer(pack_size:int):
    bin_files = glob.glob("*.bin")
    if not bin_files:
        raise FileNotFoundError("do not find any .bin file !!!")  # raise can terminate the execution
    if len(bin_files) > 1:
        raise RuntimeError(".bin file is not only one !!!")

    bin_dir = bin_files[0]
    print(f"find the target bin file {bin_dir}")
    with open(bin_dir, "rb") as f:                                # with as is context manager, close file automatically, "rb" read only binary

        pack_idx = 1
        while True:
            pack = f.read(pack_size)                              # if left bytes is less than 1024, will return all left bytes

            if not pack:
                break
            yield (pack_idx, pack)
            pack_idx += 1