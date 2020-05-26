# Check for arguments
MODEL=$1
CHECKPOINT_TAR=$2

if [ -z "$MODEL" ] || [ -z "$CHECKPOINT_TAR" ]
then
  echo "EXAMPLE USAGE: ./runmodel_fromcheckpoint.sh models.MyCustomModel models.MyCustomModel-8ShATTSPoF.pth.tar"
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
CHECKPOINT_REPLACE_PATTERN="filename='$CHECKPOINT_TAR'"

# Start training
mkdir -p $OUTPUT_DIR && # Ensure the output directory exists
git pull &&
echo "Starting training from $CHECKPOINT_TAR and redirecting output/errors to $OUTPUT_DIR/$OUTPUT_FILE" &&
sed -i "s/$MODEL_SEARCH_PATTERN/$MODEL_REPLACE_PATTERN/g" $MAIN && # Use the specified model
sed -i "s/$CHECKPOINT_SEARCH_PATTERN/$CHECKPOINT_REPLACE_PATTERN/g" $MAIN && # Unique checkpoint names
source ~/anaconda3/etc/profile.d/conda.sh &&
conda activate gazecapture &&
(sudo -E env "PATH=$PATH" nohup python $MAIN --data_path $DATA > "$OUTPUT_DIR/$OUTPUT_FILE" 2>&1 &) # Runs the script in the background, redirecting stdout/stderr to the output file
