## Initalize project
1. Create project
   ```
   mkdir match
   cd match
   poetry new match
   # poetry init
   ```
2. Install dependencies
   ```
   poetry add opencv-python
   poetry add matplotlib
   ```
3. Entry shell
   ```
   poetry shell
   ```

## Recovery project
1. Clear the old environment
   ```
   cd /path/to/project
   poetry env remove --all
   ```
2. Install
   ```
   poetry install
   ```
3. Enter shell
   ```
   poetry shell
   ```
