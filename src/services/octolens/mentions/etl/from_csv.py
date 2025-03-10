from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import modal
import polars as pl
from modal import Image

from src.services.local.filesystem import get_paths
from src.services.octolens import Mention, MentionData

if TYPE_CHECKING:
    from collections.abc import Iterator

image: Image = modal.Image.debian_slim().pip_install(
    "fastapi[standard]",
)
image.add_local_python_source(
    *[
        "src",
    ],
)
app = modal.App(
    name="",
    image=image,
)


@app.local_entrypoint()
def local(
    input_folder: str,
) -> None:
    sub_paths: list[Path] = list(get_paths(input_folder))
    df_list: list[pl.DataFrame] = [pl.read_csv(path) for path in sub_paths]
    df_full: pl.DataFrame = pl.concat(
        df_list,
        how="align",
    )
    df: pl.DataFrame = df_full.unique(
        subset=["URL"],
    )
    mention_data_list: Iterator[MentionData] = (
        MentionData.model_validate(row)
        for row in df.iter_rows(
            named=True,
        )
    )
    cwd: str = str(Path.cwd())
    output_dir: Path = Path(f"{cwd}/out/from_csv")
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )
    for count, mention_data in enumerate(
        mention_data_list,
        start=1,
    ):
        print(count)
        output_file_path: Path = output_dir / f"{count:06d}.json"
        mention: Mention = Mention(
            action="mention_created",
            data=mention_data,
        )
        with output_file_path.open(
            mode="w",
        ) as f:
            f.write(
                mention.model_dump_json(),
            )
