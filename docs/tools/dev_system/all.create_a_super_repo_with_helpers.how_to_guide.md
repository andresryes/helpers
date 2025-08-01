<!-- toc -->

- [How to Create a Super-Repo with `Helpers`](#how-to-create-a-super-repo-with-helpers)
  * [Create a New (Super) Repo in the Desired Organization](#create-a-new-super-repo-in-the-desired-organization)
  * [Add Helpers Sub-Repo](#add-helpers-sub-repo)
  * [Copy and Customize Files in the Top Dir](#copy-and-customize-files-in-the-top-dir)
    + [Copy Files From Existing Repo](#copy-files-from-existing-repo)
    + [Script Approach](#script-approach)
    + [Manual Approach](#manual-approach)
  * [Copy and Customize Files in `Thin_Client`](#copy-and-customize-files-in-thin_client)
    + [Copy Files From Existing Repo](#copy-files-from-existing-repo-1)
    + [Script Approach](#script-approach-1)
    + [Manual Approach](#manual-approach-1)
  * [Build and Test the Thin Environment](#build-and-test-the-thin-environment)
    + [Build the Thin Environment](#build-the-thin-environment)
    + [Test the Thin Environment](#test-the-thin-environment)
    + [Create the Tmux Links](#create-the-tmux-links)
  * [Copy and Customize Files in `Devops`](#copy-and-customize-files-in-devops)
  * [Create Symbolic Links](#create-symbolic-links)
  * [5) Build Container and Running Tests](#5-build-container-and-running-tests)
    + [Build a Container for a Super-Repo](#build-a-container-for-a-super-repo)
    + [Check If the Regressions Are Passing](#check-if-the-regressions-are-passing)
  * [Configure Regressions Via Github Actions](#configure-regressions-via-github-actions)
    + [Set Repository Secrets/Variables](#set-repository-secretsvariables)
    + [Create Github Actions Workflow Files](#create-github-actions-workflow-files)
    + [Configure Gitleaks Scan](#configure-gitleaks-scan)
  * [Configure Github Repo](#configure-github-repo)

<!-- tocstop -->

# How to Create a Super-Repo with `Helpers`

## Create a New (Super) Repo in the Desired Organization

- Create a repo within the
  [`causify-ai` organization](https://github.com/causify-ai)
- Follow the
  [official guide](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository#creating-a-new-repository-from-the-web-ui)
  - TODO(Grisha): consider using repository
    [templates](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template)
- Recommended options:
  - Owner: `causify-ai`
  - Repository-name: provide a valid short name, e.g., `algo_trading`
  - Visibility: by default choose `Private`
  - Add a README file
  - `.gitignore template: None`
  - License: `General Public License v3.0`

## Add Helpers Sub-Repo

- Below there is an example for the `//helpers` repo, but it works for any repo
  (e.g., `//orange`) including any other repo (e.g., `//cmamp`)

- Clone the super-repo locally

  ```bash
  > git clone --recursive git@github.com:causify-ai/{repo_name}.git ~/src/{repo_name}{index}
  ```

- Checkout to a new branch

  ```bash
  > git checkout -b repo_init
  ```

- Add a submodule

  ```bash
  > cd ~/src/repo_name1
  # In general form.
  # > git submodule add {submodule_url} {submodule_path}
  # Example for `cmamp`.
  > git submodule add git@github.com:causify-ai/helpers.git helpers_root
  ```

- The command will create a `.gitmodules` file that we need to check-in:

  ```text
  [submodule "helpers_root"]
  path = helpers_root
  url = git@github.com:causify-ai/helpers.git
  ```

- Init the submodule and commit the `.gitmodules` file

  ```bash
  > git submodule init
  > git submodule update
  ```

- Commit and push the changes
  ```bash
  > git add .gitmodules helpers_root
  > git commit -am "Add helpers subrepo" && git push
  ```

## Copy and Customize Files in the Top Dir

- Conceptually you need to copy and customize the files in:

  1. `thin_client` (one can reuse the thin client across repos)
  2. The top dir (to run `pytest`, ...)
  3. `devops` (to build the dev and prod containers)
  4. `.github/workflows` (to run the GitHub regressions)

- After copying the files you can search for the string `xyz` to customize

- If there is a problem with phases 3) and 4) due to the thin environment not
  being completely configured, you can keep moving and then re-run the command
  later

### Copy Files From Existing Repo

- Copy the files from a working repo (e.g., `//cmamp`)

  ```bash
  > export SRC_DIR=$HOME/src/cmamp1
  > ls $SRC_DIR

  > cp $SRC_DIR/{pytest.ini,repo_config.yaml,tasks.py} .
  > vi pytest.ini repo_config.yaml tasks.py
  ```

### Script Approach

- Customize the script
  [`/dev_scripts_helpers/thin_client/sync_super_repo.sh`](/dev_scripts_helpers/thin_client/sync_super_repo.sh)
  ```
  DST_PREFIX="umd_msml610"
  ```
- Run the script which allows to `vimdiff` / `cp` files across a super-repo and
  its `//helpers` dir

### Manual Approach

- Some files need to be copied from `//helpers` to the root of the super-repo to
  configure various tools (e.g., dev container workflow, `pytest`, `invoke`)
  - `pytest.ini`: configure `pytest` preferences
  - `repo_config.yaml`: stores information about this specific repo (e.g., name,
    used container, runnable dir config)
    - This needs to be modified
    ```yaml
    repo_info:
      repo_name: cmamp
    ...
    docker_info:
      docker_image_name: cmamp
    ...
    runnable_dir_info:
      use_helpers_as_nested_module: 1
      ...
      dir_suffix: cmamp
    ```
  - `tasks.py`: the `invoke` tasks available in this container
    - This can be modified if needed

- You can copy all these files from `//helpers`
  ```bash
  > cp helpers_root/{pytest.ini,repo_config.yaml,tasks.py} .
  > vim pytest.ini repo_config.yaml tasks.py
  ```

## Copy and Customize Files in `Thin_Client`

### Copy Files From Existing Repo

- Copy the files from a working repo (e.g., `//cmamp`)

  ```bash
  > export SRC_DIR=$HOME/src/cmamp1
  > ls $SRC_DIR

  > cp $SRC_DIR/{pytest.ini,repo_config.yaml,tasks.py} .
  > vi pytest.ini repo_config.yaml tasks.py
  ```

### Script Approach

- Customize the script
  [`/dev_scripts_helpers/thin_client/sync_super_repo.sh`](/dev_scripts_helpers/thin_client/sync_super_repo.sh)
  ```
  DST_PREFIX="umd_msml610"
  ```
- Run the script which allows to `vimdiff` / `cp` files across a super-repo and
  its `//helpers` dir

### Manual Approach

- Create the `dev_scripts_{dir_name}` dir based off the template from `helpers`

  ```bash
  # Use a suffix based on the repo name, e.g., `tutorials`, `sports_analytics`.
  > SRC_DIR="./helpers_root/dev_scripts_helpers/thin_client"; ls $SRC_DIR
  > DST_SUFFIX="xyz"
  > DST_DIR="dev_scripts_${DST_SUFFIX}/thin_client"; echo $DST_DIR
  > mkdir -p $DST_DIR
  > cp -r $SRC_DIR/{build.py,requirements.txt,setenv.sh,tmux.py} $DST_DIR
  ```

- The resulting `dev_scripts_{dir_name}` should look like:

  ```bash
  > ls -1 $DST_DIR
  build.py
  requirements.txt
  setenv.sh
  tmux.py
  ```

- If we don't need to create a new thin env, then you can delete the files
  `dev_scripts_{dir_name}/thin_client/build.py` and `requirements.txt`

## Build and Test the Thin Environment

### Build the Thin Environment

- Build the thin environment:
  ```
  > $DST_DIR/build.py
  ... ==> `brew cleanup` has not been run in the last 30 days, running now...
  ... Disable this behaviour by setting HOMEBREW_NO_INSTALL_CLEANUP.
  ... Hide these hints with HOMEBREW_NO_ENV_HINTS (see `man brew`).
  14:37:37 - INFO  build.py _main:94                  # gh version=gh version 2.58.0 (2024-10-01)
  https://github.com/cli/cli/releases/tag/v2.58.0
  14:37:37 - INFO  build.py _main:100                 /Users/saggese/src/quant_dashboard1/dev_scripts_quant_dashboard/thin_client/build.py successful
  ```

### Test the Thin Environment

- Follow
  [the on-boarding guide](/docs/onboarding/ck.development_setup.how_to_guide.md#set-up-the-thin-environment)

### Create the Tmux Links

- Follow
  [the on-boarding guide](/docs/onboarding/ck.development_setup.how_to_guide.md#create-a-tmux-session)

## Copy and Customize Files in `Devops`

- Copy the `devops` template dir
  ```bash
  > (cd helpers_root; git pull)
  > cp -r helpers_root/devops devops
  ```
- If we don't need to build a container and just we can reuse, then we can
  delete the corresponding `build` directory

  ```bash
  > rm -rf devops/docker_build
  ```

- Follow the instructions in
  [`/docs/tools/dev_system/all.devops_docker.reference.md`](/docs/tools/dev_system/all.devops_docker.reference.md)
  and
  [`/docs/tools/dev_system/all.devops_docker.how_to_guide.md`](/docs/tools/dev_system/all.devops_docker.how_to_guide.md)

## Create Symbolic Links

- Check the difference between the super-repo and `helpers`

  ```bash
  > helpers_root/dev_scripts_helpers/thin_client/sync_super_repo.sh
  ```

- Replace file with symbolic links:

  ```bash
  > echo $SRC_DIR
  ./helpers_root/dev_scripts_helpers/thin_client
  > echo $DST_DIR
  ./dev_scripts_xyz/thin_client
  > ./helpers_root/helpers/create_links.py --src_dir $SRC_DIR --dst_dir $DST_DIR --replace_links --use_relative_paths
  ```

- Refer to
  [Managing common files](/docs/tools/dev_system/all.runnable_repo.reference.md#managing-common-files)
  for explanation
- Refer to
  [Managing symbolic links between directories](/docs/tools/dev_system/all.replace_common_files_with_script_links.md)
  for how to use the commands

## 5) Build Container and Running Tests

### Build a Container for a Super-Repo

- Run the single-arch flow:

  ```bash
  > i docker_build_local_image --version 1.0.0 && i docker_tag_local_image_as_dev --version 1.0.0
  > i docker_bash --skip-pull
  > i docker_jupyter
  ```

- Run the multi-arch flow:

  ```bash
  > i docker_build_local_image --version 1.0.0 --multi-arch "linux/amd64,linux/arm64"
  > i docker_tag_local_image_as_dev --version 1.0.0
  ```

- If you wish to push the dev image to a remote registry, contact the infra team
  to add new registry with default settings
  - Make sure the registry name matches the repo name for consistency
  - By default we add new containers to Stockholm region (`eu-north-1`)

### Check If the Regressions Are Passing

- Follow
  [the on-boarding doc](/docs/onboarding/ck.development_setup.how_to_guide.md#begin-working)
  to confirm that everything is set up properly

- File a PR with the new files and merge the PR into `master`

## Configure Regressions Via Github Actions

### Set Repository Secrets/Variables

- Some secrets/variables are shared in an organization wide storage
  - E.g. for [Causify](https://github.com/organizations/causify-ai) at
    [https://github.com/organizations/causify-ai/settings/secrets/actions](https://github.com/organizations/causify-ai/settings/secrets/actions)
  - These values are shared across all repos in the organization so we don't
    need to create them on a per-repo basis
    - The access method is the same as for per-repo variables - via actions
      context `${{ secrets.MY_TOKEN }}` or ``${{ vars.MY_TOKEN }}`
  - Once a `secret` is set it's read-only for everybody. To preview all of the
    raw values that are currently used, visit
    [1password > Shared vault > Causify org GH actions secrets](https://causify.1password.com/app#/everything/AllItems/ofre2i2yhv2lyf7ggvv2a4uouaaxvzjzaomv3hol24txn2an5imq)

- Before adding a new secret/variables for a repo, consider the following:
  - If it's already present in the global storage for an organization, no action
    is required
  - If it's not, check if the newly added value is not needed in all of the
    repos, if so, add it to the global storage to facilitate reusability
    - If you lack permissions for this operation, contact your TL

- Should a repo need some additional secret values/variables, follow the
  procedure below

1. Login to 1password
   [https://causify.1password.com/home](https://causify.1password.com/home)
   - Ask your TL if you don't have access to 1password
2. Navigate to the `Shared Vault`
3. Search for `Github actions secrets JSON` secret
4. Copy the JSON from 1password to a temporary local file `vars.json`
5. Run the script to set the secrets/variables
   ```bash
   > cd ~/src/<REPO_NAME>
   > ./helpers_root/dev_scripts_helpers/github/set_secrets_and_variables.py \
        --file `vars.json' \
        --repo '<ORG_NAME>/<REPO_NAME>'
   ```
6. Make sure not to commit the raw `vars.json` file or the
   [`/dev_scripts_helpers/github/set_secrets_and_variables.py.log`](/dev_scripts_helpers/github/set_secrets_and_variables.py.log)
   file

- Delete those files locally

### Create Github Actions Workflow Files

1. Create a directory `./github/workflows` in the super-repo
2. Copy an example flow from helpers
   - E.g. `helpers_root/.github/workflows/fast_tests.yml
   - Modify it based on your needs
     - Find and replace mentions of `helpers` with the name of super repo for
       consistency
     - Replace `invoke run_fast_tests` with your desired action

### Configure Gitleaks Scan

- Copy the configuration and workflow files

  ```bash
  > cp ./helpers_root/.github/gitleaks-rules.toml ./.github
  > cp ./helpers_root/.github/workflows/gitleaks.yml ./.github/workflows
  ```

- Replace files with symbolic links

  ```bash
  > ./helpers_root/helpers/create_links.py --src_dir ./helpers_root/.github --dst_dir ./.github --replace_links --use_relative_paths
  ```

- Note:
  - Only the `gitleaks-rules.toml` file should be replaced with symbolic links
  - The `gitleaks.yml` file should be copied as is because GitHub Actions does
    not resolve symbolic links when parsing workflows in the `.github/workflows`
    directory (See #CmampTask11429)

## Configure Github Repo

- **Disclaimer**: the following set-up requires paid GitHub version (Pro / Team
  / Enterprise)

- Set-up branch protection rule for master
  - Navigate to `https://github.com/<your org>/<<your-repo>>/settings/branches`
  - Click "Add rule"
    - Specify branch name pattern `master`
    - Check the following options:
      - `Require a pull request before merging` (do not check the sub-options)
      - `Require status checks to pass before merging`
        - Check the `Require branches to be up to date before merging`
          sub-option
        - In the `Status checks that are required` table specify the workflows
          you want to pass before merging each PR
          - Depends on which workflows were set-up in the step above
          - Usually its `run_fast_tests` and `run_slow_tests`
      - `Require conversation resolution before merging`
    - Click "Save changes" button

- You need to sync the repo using the sync script
