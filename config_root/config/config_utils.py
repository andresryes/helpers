"""
Import as:

import config_root.config.config_utils as crcocout
"""

import argparse
import collections
import copy
import logging
import os
import re
from typing import Any, Iterable, List, Optional

try:
    from collections.abc import (
        Hashable as AbcHashable,
        Mapping as AbcMapping,
        Iterable as AbcIterable,
    )
except ImportError:
    from collections import (
        Hashable as AbcHashable,
        Mapping as AbcMapping,
        Iterable as AbcIterable,
    )

import pandas as pd

import config_root.config.config_ as crococon
import helpers.hdbg as hdbg
import helpers.hdict as hdict
import helpers.hdocker as hdocker
import helpers.hio as hio
import helpers.hpickle as hpickle
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)


# #############################################################################
# Configs.
# #############################################################################


def validate_configs(configs: List[crococon.Config]) -> None:
    """
    Assert if the list of configs contains duplicates.
    """
    hdbg.dassert_container_type(configs, List, crococon.Config)
    hdbg.dassert_no_duplicates(
        list(map(str, configs)), "There are duplicate configs in passed list"
    )


def configs_to_str(configs: List[crococon.Config]) -> str:
    """
    Print a list of configs into a readable string.
    """
    txt = []
    for i, config in enumerate(configs):
        txt.append(f"# {i + 1}/{len(configs)}")
        txt.append(hprint.indent(str(config)))
    res = "\n".join(txt)
    return res


def replace_shared_dir_paths(
    config: crococon.Config, *, replace_ecs_tokyo: Optional[bool] = False
) -> crococon.Config:
    """
    Replace all the root paths of the shared data directory in the config.

    :param config: config to update
    :param replace_ecs_tokyo: if True replace `ecs_tokyo` to `ecs` in the path
    :return: updated version of a config
    """
    new_config = config.copy()
    initial_update_mode = new_config.update_mode
    # Update mode should be set to "overwrite" to allow the changes in the
    # config.
    new_config.update_mode = "overwrite"
    for key in config.keys():
        value = config[key]
        if isinstance(value, crococon.Config):
            value = replace_shared_dir_paths(
                value, replace_ecs_tokyo=replace_ecs_tokyo
            )
        elif isinstance(value, str):
            # Search for file paths among string values only.
            value = hdocker.replace_shared_root_path(
                value, replace_ecs_tokyo=replace_ecs_tokyo
            )
        else:
            # No need to change values other than strings.
            pass
        new_config[key] = value
    new_config.update_mode = initial_update_mode
    return new_config


# TODO(gp): Add unit tests.
def sort_config_string(txt: str) -> str:
    """
    Sort a string representing a Config in alphabetical order by the first
    level.

    This function can be used to diff two Configs serialized as strings.
    """
    lines = [line.rstrip("\n") for line in txt]
    # Parse.
    chunks = {}
    state = "look_for_start"
    start_idx = end_idx = None
    for i, line in enumerate(lines):
        _LOG.debug(
            f"i={i} state={state} start_idx={start_idx} end_idx={end_idx} line={line}"
        )
        if (
            state == "look_for_start"
            and line[0] != " "
            and lines[i + 1][0] != " "
        ):
            _LOG.debug("Found single line")
            # Single line.
            key = lines[i]
            val = " "
            chunks[key] = val
            _LOG.debug("Single line -> %s %s", key, val)
        elif state == "look_for_start" and line[0] != " ":
            _LOG.debug("Found first line")
            start_idx = i
            end_idx = None
            state = "look_for_end"
        elif state == "look_for_end" and line[0] != " ":
            _LOG.debug("Found last line")
            end_idx = i - 1
            hdbg.dassert_lte(start_idx, end_idx)
            key = lines[start_idx]
            _LOG.debug("start_idx=%s end_idx=%s key=%s", start_idx, end_idx, key)
            val = lines[start_idx + 1 : end_idx + 1]
            chunks[key] = val
            _LOG.debug("-> %s %s", key, val)
            #
            state = "look_for_start"
            start_idx = i
            end_idx = None
    # Sort.
    chunks = {k: chunks[k] for k in sorted(chunks.keys())}
    # Assemble with proper indentation.
    chunks = "\n".join(
        [k + hprint.indent("\n".join(chunks[k])) for k in chunks.keys()]
    )
    return chunks


def load_config_from_pickle1(log_dir: str, tag: str) -> crococon.Config:
    """
    Load config from a pickle file.

    :param log_dir: path to execution logs
    :param tag: basename of the pickle file (e.g.,
        "system_config.output")
    :return: config object
    """
    hdbg.dassert_dir_exists(log_dir)
    # TODO(Grisha): centralize version file name somehow, e.g., move to the `Config` class.
    # Build path to config version file.
    config_version_filename = "config_version.txt"
    config_version_path = os.path.join(log_dir, config_version_filename)
    if os.path.exists(config_version_path):
        # Extract config version from the corresponding file.
        config_version = hio.from_file(config_version_path)
        # TODO(Grisha): centralize file name, e.g., move to the `Config` class.
        # Set file name that corresponds to the extracted config version.
        file_name = f"{tag}.all_values_picklable.pkl"
        config_path = os.path.join(log_dir, file_name)
    else:
        # Only v2 config version has no version file.
        config_version = "v2"
        # Set file name corresponding to v2 config version.
        file_name = f"{tag}.values_as_strings.pkl"
    _LOG.info(f"Found Config {config_version} flow")
    # Get config from file.
    config_path = os.path.join(log_dir, file_name)
    hdbg.dassert_path_exists(config_path)
    _LOG.debug("Reading config from %s", config_path)
    config = hpickle.from_pickle(config_path)
    if isinstance(config, dict):
        # _LOG.warning("Found Config v1.0 flow: converting")
        # config = crococon.Config.from_dict(config)
        raise TypeError(
            f"Found Config v1.0 flow at '{config_path}'. Deprecated in CmTask7794."
        )
    return config


# TODO(Dan): Replace with `load_config_from_pickle1()` in CmTask7795.
def load_config_from_pickle(config_path: str) -> crococon.Config:
    """
    Load config from pickle file.
    """
    hdbg.dassert_path_exists(config_path)
    _LOG.debug("Reading config from %s", config_path)
    config = hpickle.from_pickle(config_path)
    if isinstance(config, dict):
        # _LOG.warning("Found Config v1.0 flow: converting")
        # config = crococon.Config.from_dict(config)
        raise TypeError(
            f"Found Config v1.0 flow at '{config_path}'. Deprecated in CmTask7794."
        )
    return config


def apply_config(
    config: crococon.Config,
    set_config_values: Optional[List[str]],
    *,
    clobber_mode: str = "assert_on_write_after_use",
) -> crococon.Config:
    """
    Update the values in a config with the passed values.

    The change is done inplace.

    :param config: config to update
    :param set_config_values: string representation of 2 tuples separated
        by comma. The first tuple has 1 or more string keys separated by commas.
        The second tuple contains a string representation of a value to replace.
        Pattern: '("key1, key2, ..."),("value_to_replace")'
        E.g.,
        `("target_gmv"),(int(10000))`
        `("portfolio", "style"),("longitudinal")`
        `("portfolio", "val"),(int(3))`
    :param ignore_clobber_mode: allow to overwrite used values in the config if
        set to True, overwise do not
    :return: updated version of a config
    """
    _LOG.debug("set_config_values=%s", set_config_values)
    if set_config_values is not None:
        # Allow to overwrite config values for the function execution.
        initial_config_update_mode = config.update_mode
        config.update_mode = "overwrite"
        initial_clobber_mode = config.clobber_mode
        if clobber_mode != initial_clobber_mode:
            _LOG.debug(
                "changing config.clobber_mode from %s to %s",
                initial_clobber_mode,
                clobber_mode,
            )
            config.clobber_mode = clobber_mode
        for config_val in set_config_values:
            _LOG.debug("config_val=%s", config_val)
            # E.g., `("foo","bar"),(bool("True"))``.
            re_pattern = r"^\(([^()]+)\),\((.*)\)$"
            match = re.match(re_pattern, config_val)
            hdbg.dassert_ne(
                match,
                None,
                msg=f"No match is found for config_val={config_val}.",
            )
            n_groups_matches = len(match.groups())
            hdbg.dassert_eq(
                2,
                n_groups_matches,
                msg=f"Must be exactly 2 groups matched, found={n_groups_matches}",
            )
            # TODO(Dan): `key` -> `compound_key`?
            key, value = match.groups()
            # Convert the key into a tuple.
            key = eval("(" + key + ")")
            # Run the Python expression to handle types, e.g., (int(3)).
            new_value = eval(value)
            # TODO(Grisha): not sure we want to pass a `Dict`.
            if isinstance(new_value, dict):
                # Convert to a `Config` because a config's value cannot be a dict.
                new_value = crococon.Config.from_dict(new_value)
            # Inform a user about the override.
            if key in config:
                old_value = config[key]
                if new_value != old_value:
                    _LOG.warning(
                        "Overwriting compound_key=%s old_value=%s with new_value=%s",
                        key,
                        old_value,
                        new_value,
                    )
            # TODO(Dan): We may want to assert if `compound_key` is in config.
            # Otherwise we always risk a silent append of a useless param to config.
            else:
                _LOG.warning(
                    "Adding a new compound_key=%s value=%s",
                    key,
                    new_value,
                )
            # TODO(Grisha): use `config.update()` instead of `config[key] = value`.
            config[key] = new_value
        if initial_clobber_mode != clobber_mode:
            _LOG.debug(
                "changing config.clobber_mode from %s to %s",
                clobber_mode,
                initial_clobber_mode,
            )
            config.clobber_mode = initial_clobber_mode
        # Set back the initial config update mode.
        config.update_mode = initial_config_update_mode
    return config


def apply_config_overrides_from_command_line(
    config: crococon.Config,
    args: argparse.Namespace,
) -> crococon.Config:
    """
    Update the values in a config using the command line options.

    The change is done inplace.

    :param config: config to update
    :param args: cmd line parameters, see `apply_config()` for
        "set_config_value" arg format
    :return: updated version of a config
    """
    args_dict = vars(args)
    _LOG.debug("args_dict=%s", args_dict)
    if "set_config_value" in args_dict:
        set_config_value = args_dict["set_config_value"]
        _LOG.info("set_config_value=%s", set_config_value)
        config = apply_config(config, set_config_value)
    return config


def add_config_override_args(
    parser: argparse.ArgumentParser,
) -> argparse.ArgumentParser:
    parser.add_argument(
        "--set_config_value",
        action="append",
        help="See `apply_config()` for detailed description.",
        type=str,
    )
    return parser


# #############################################################################


# TODO(gp): This could be a method of Config to encapsulate.
def check_no_dummy_values(config: crococon.Config) -> bool:
    """
    Assert if there are no `crococon.DUMMY` values.
    """
    dummy_type = type(crococon.DUMMY)
    _LOG.debug("type(DUMMY)=%s", dummy_type)
    for key, val in hdict.get_nested_dict_iterator(config.to_dict()):
        # (k, v) looks like:
        # ```
        # (('load_prices', 'source_node_name'), 'kibot_equities')
        # ```
        _LOG.debug(hprint.to_str("key val"))
        # Only check for equality if the types agree.
        # Example: if we compare a pd.Series to a built-in type, the comparison
        # is carried out element-wise, which is not what we want in this case.
        if isinstance(val, dummy_type):
            hdbg.dassert_ne(
                val,
                crococon.DUMMY,
                "DUMMY value %s detected along %s",
                str(val),
                str(key),
            )
    return True


# #############################################################################


def make_hashable(obj: Any) -> AbcHashable:
    """
    Coerce `obj` to a hashable type if not already hashable.
    """
    ret = None
    if isinstance(obj, AbcMapping):
        # Handle dict-like objects.
        new_object = copy.deepcopy(obj)
        for k, v in new_object.items():
            new_object[k] = make_hashable(v)
        ret = tuple(new_object.items())
    elif isinstance(obj, AbcIterable) and not isinstance(obj, str):
        # The problem is that `str` is both `Hashable` and `Iterable`, but here
        # we want to treat it like `Hashable`, i.e. return string as it is.
        # Same with `Tuple`, but for `Tuple` we want to apply the function
        # recursively, i.e. make every element `Hashable`.
        ret = tuple([make_hashable(element) for element in obj])
    elif isinstance(obj, AbcHashable):
        # Return the object as is, since it's already hashable.
        ret = obj
    else:
        ret = tuple(obj)
    return ret


def intersect_configs(configs: Iterable[crococon.Config]) -> crococon.Config:
    """
    Return a config formed by taking the intersection of configs.

    - Key insertion order is not taken into consideration for the purpose of
      calculating the config intersection
    - The key insertion order of the returned config will respect the key
      insertion order of the first config passed in
    """
    # Flatten configs and convert to sets for intersection.
    # We create a list so that we can reference a flattened config later.
    flattened = [c.flatten() for c in configs]
    hdbg.dassert(flattened, "Empty iterable `configs` received.")
    # Obtain a reference config.
    # The purpose of this is to ensure that the config intersection respects a key
    # ordering. We also make this copy so as to maintain the original (not
    # necessarily hashable) values.
    reference_config = flattened[0].copy()
    # Make values hashable.
    for flat in flattened:
        for k, v in flat.items():
            flat[k] = make_hashable(v)
    sets = [set(c.items()) for c in flattened]
    intersection_of_flattened = set.intersection(*sets)
    # Create intersection.
    # Rely on the fact that Config keys are of type `str`.
    intersection = crococon.Config()
    for k, v in reference_config.items():
        if (k, make_hashable(v)) in intersection_of_flattened:
            intersection[k] = v
    return intersection


# TODO(gp): This could be a method of Config.
def subtract_config(
    minuend: crococon.Config, subtrahend: crococon.Config
) -> crococon.Config:
    """
    Return a `Config` defined via minuend - subtrahend.

    :return: return a `Config` with (path, val pairs) in `minuend` that are not in
        `subtrahend` (like a set difference). Equivalently, return a `Config`-like
        `minuend` but with the intersection of `minuend` and `subtrahend`
        removed.
    """
    hdbg.dassert(minuend)
    flat_m = minuend.flatten()
    flat_s = subtrahend.flatten()
    diff = crococon.Config()
    for k, v in flat_m.items():
        if (k not in flat_s) or (flat_m[k] != flat_s[k]):
            # It is not possible to use a dict as a config's value.
            # It should be converted to a config first.
            if isinstance(v, dict):
                if not v:
                    # Replace empty dict with empty config.
                    v = crococon.Config()
                else:
                    # Get config from a dict.
                    v = crococon.Config.from_dict(v)
            diff[k] = v
    return diff


def diff_configs(configs: Iterable[crococon.Config]) -> List[crococon.Config]:
    """
    Diff `Config`s with respect to their common intersection.

    :return: for each config `config` in `configs`, return a new `Config` consisting
        of the part of `config` not in the intersection of the configs
    """
    # Convert the configs to a list for convenience.
    configs = list(configs)
    # Find the intersection of all the configs.
    intersection = intersect_configs(configs)
    # For each config, compute the diff between the config and the intersection.
    config_diffs = []
    for config in configs:
        config_diff = subtract_config(config, intersection)
        config_diffs.append(config_diff)
    hdbg.dassert_eq(len(config_diffs), len(configs))
    return config_diffs


# #############################################################################


# TODO(gp): Is this private?
def convert_to_series(config: crococon.Config) -> pd.Series:
    """
    Convert a config into a flattened series representation.

    - This is lossy but useful for comparing multiple configs
    - `str` tuple paths are joined on "."
    - Empty leaf configs are converted to an empty tuple
    """
    hdbg.dassert_isinstance(config, crococon.Config)
    hdbg.dassert(config, msg="`config` is empty")
    flat = config.flatten()
    keys: List[str] = []
    vals: List[tuple] = []
    for k, v in flat.items():
        key = ".".join(k)
        keys.append(key)
        if isinstance(v, crococon.Config):
            vals.append(())
        else:
            vals.append(v)
    hdbg.dassert_no_duplicates(keys)
    srs = pd.Series(index=keys, data=vals)
    return srs


# TODO(gp): Is this private?
def convert_to_dataframe(configs: Iterable[crococon.Config]) -> pd.DataFrame:
    """
    Convert multiple configs into flattened dataframe representation.
    """
    hdbg.dassert_isinstance(configs, Iterable)
    srs = list(map(convert_to_series, configs))
    hdbg.dassert(srs)
    df = pd.concat(srs, axis=1).T
    return df


def build_config_diff_dataframe(
    config_dict: collections.OrderedDict, tag_col: Optional[str] = None
) -> pd.DataFrame:
    """
    Create a dataframe of config diffs.

    :param config_dict: dictionary of configs
    :param tag_col: name of the tag col. If tags are the same for all configs
        and `tag_col` is not None, add tags to config diffs dataframe
    :return: config diffs dataframe
    """
    # Convert the dict into a list of tuples (key, value).
    diffs = diff_configs(config_dict.values())
    _LOG.debug("diffs=\n%s", configs_to_str(diffs))
    # Remove empty configs.
    non_empty_diffs = [
        (k, v)
        for (diff, k, v) in zip(diffs, config_dict.keys(), config_dict.values())
        if len(diff) > 0
    ]
    if non_empty_diffs:
        config_diffs = convert_to_dataframe(diffs).dropna(how="all", axis=1)
    else:
        config_diffs = pd.DataFrame(index=range(len(diffs)))
    # If tags are the same, still add them to `config_diffs`.
    if tag_col is not None and tag_col not in config_diffs.columns:
        tags = [config[tag_col] for config in config_dict.values()]
        config_diffs[tag_col] = tags
    return config_diffs
