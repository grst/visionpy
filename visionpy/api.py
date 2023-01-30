from typing import Literal, Optional, Sequence, Union

import anndata
import click
import scanpy as sc
from sklearn.preprocessing import normalize

from visionpy import create_app, data_accessor

from .signature import compute_signature_anndata


def _prepare_vision(
    adata: Union[str, anndata.AnnData],
    name: str,
    norm_data_key: Optional[Union[Literal["use_raw"], str]] = None,
    compute_neighbors_on_key: Optional[str] = None,
    signature_varm_key: Optional[str] = None,
    signature_names_uns_key: Optional[str] = None,
    signatures_files: Sequence[str] = None,
):
    if isinstance(adata, str):
        adata = anndata.read(str)

    if compute_neighbors_on_key is not None:
        sc.pp.neighbors(adata, use_rep=compute_neighbors_on_key)
    else:
        # TODO: check that neighbors is in anndata
        pass

    # row normalize connectivity
    adata.obsp["normalized_connectivities"] = normalize(
        adata.obsp["connectivities"], norm="l1", axis=1
    )
    adata.uns["vision_session_name"] = name

    data_accessor.adata = adata
    data_accessor.norm_data_key = norm_data_key
    data_accessor.signature_varm_key = signature_varm_key
    data_accessor.signature_names_uns_key = signature_names_uns_key
    data_accessor.compute_obs_df_scores()
    data_accessor.compute_one_vs_all_obs_cols()

    # compute signatures
    if signature_varm_key is not None:
        compute_signature_anndata(
            adata,
            norm_data_key,
            signature_varm_key,
            signature_names_uns_key,
        )
        data_accessor.compute_signature_scores()
        data_accessor.compute_one_vs_all_signatures()
        data_accessor.compute_gene_score_per_signature()


def start_vision(
    adata: Union[str, anndata.AnnData],
    name: str,
    norm_data_key: Optional[Union[Literal["use_raw"], str]] = None,
    compute_neighbors_on_key: Optional[str] = None,
    signature_varm_key: Optional[str] = None,
    signature_names_uns_key: Optional[str] = None,
    signatures_files: Sequence[str] = None,
    port: Optional[int] = None,
    debug: bool = False,
):
    """Wrapper function to start VISION server.

    Parameters
    ----------
    adata
        AnnData object
    name
        Name for the VISION session
    norm_data_key
        Key for layer with log library size normalized data. If
        `None` (default), uses `adata.X`
    compute_neighbors_on_key
        Key in `adata.obsm` to use for computing neighbors. If `None`, use
        neighbors stored in `adata`. If no neighbors have been previously
        computed an error will be raised.
    port
        The port of the webserver. Defaults to 5000.
    """
    _prepare_vision(
        adata=adata,
        name=name,
        norm_data_key=norm_data_key,
        compute_neighbors_on_key=compute_neighbors_on_key,
        signature_varm_key=signature_varm_key,
        signature_names_uns_key=signature_names_uns_key,
        signatures_files=signatures_files,
    )
    app = create_app()
    app.run(threaded=False, processes=1, debug=debug, port=port)


@click.command()
@click.option("--adata", prompt="Path to anndata.", help="Test")
@click.option("--name", prompt="Name of VISION session.")
@click.option("--norm_data_key", default=None, prompt="Name of VISION session.")
@click.option(
    "--compute_neighbors_on_key", default=None, prompt="Name of VISION session."
)
@click.option("--debug", default=False, prompt="Name of VISION session.")
def _start_vision_cli(adata, name, norm_data_key, compute_neighbors_on_key, debug):
    start_vision(adata, name, norm_data_key, compute_neighbors_on_key, debug)
