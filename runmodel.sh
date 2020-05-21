# Check for arguments
MODEL=$1

if [ -z "$MODEL" ]
then
  echo "EXAMPLE USAGE: ./runmodel.sh models.MyCustomModel"
  exit 1
fi

# Constants
DATA="/datadrive/gazecapture-dataset-prepared"
MAIN="/home/wtang06/gazecapture/gazecapture-cse455/main.py"
DEFAULT_MODEL="models.ITrackerModelOriginal"

OUTPUT_DIR="/home/wtang06/gazecapture/gazecapture-cse455/logs"
OUTPUT_FILE="$MODEL-$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c10).txt" # Generate a random file name prefixed with the model name

SEARCH_PATTERN="from models\..* import ITrackerModel"
REPLACE_PATTERN="from $MODEL import ITrackerModel"

# Start training
mkdir -p $OUTPUT_DIR && # Ensure the output directory exists
git pull &&
echo "Starting training and redirecting output/errors to $OUTPUT_DIR/$OUTPUT_FILE" &&
sed -i "s/$SEARCH_PATTERN/$REPLACE_PATTERN/g" $MAIN && # Use the specified model
source ~/anaconda3/etc/profile.d/conda.sh &&
conda activate gazecapture &&
(sudo -E env "PATH=$PATH" nohup python $MAIN --data_path $DATA --reset > "$OUTPUT_DIR/$OUTPUT_FILE" 2>&1 &) # Runs the script in the background, redirecting stdout/stderr to the output file
