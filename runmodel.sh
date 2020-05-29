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

IDENTIFIER="$MODEL-$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c10)" # Generate a unique identifier for this run
OUTPUT_DIR="/home/wtang06/gazecapture/gazecapture-cse455/logs"
OUTPUT_FILE="$IDENTIFIER.txt" # Generate a random file name prefixed with the model name

MODEL_SEARCH_PATTERN="from models\..* import ITrackerModel"
MODEL_REPLACE_PATTERN="from $MODEL import ITrackerModel"

CHECKPOINT_SEARCH_PATTERN="filename='.*'"
CHECKPOINT_REPLACE_PATTERN="filename='$IDENTIFIER.pth.tar'"
CHECKPOINTS_PATH="/home/wtang06/gazecapture/gazecapture-cse455/checkpoints" # This should be the same as CHECKPOINTS_PATH in main.py

# Start training
mkdir -p $OUTPUT_DIR && # Ensure the log output directory exists
mkdir -p $CHECKPOINTS_PATH && # Ensure the checkpoint output directory exists
git checkout $MAIN && # Go back to the main.py before any of our replacements
git pull &&
echo "Starting training and redirecting output/errors to $OUTPUT_DIR/$OUTPUT_FILE" &&
echo "...the checkpoint will be saved in $CHECKPOINTS_PATH/$IDENTIFIER.pth.tar" &&
sed -i "s/$MODEL_SEARCH_PATTERN/$MODEL_REPLACE_PATTERN/g" $MAIN && # Use the specified model
sed -i "s/$CHECKPOINT_SEARCH_PATTERN/$CHECKPOINT_REPLACE_PATTERN/g" $MAIN && # Unique checkpoint names
source ~/anaconda3/etc/profile.d/conda.sh &&
conda activate gazecapture &&
(sudo -E env "PATH=$PATH" nohup python $MAIN --data_path $DATA --reset > "$OUTPUT_DIR/$OUTPUT_FILE" 2>&1 &) # Runs the script in the background, redirecting stdout/stderr to the output file
