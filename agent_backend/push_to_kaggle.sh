#!/bin/bash

# Ensure we are in the right directory
cd "$(dirname "$0")"

# Activate the virtual environment so we don't hit the Arch Linux PEP 668 error
source venv/bin/activate

# Check if kaggle is installed
if ! command -v kaggle &> /dev/null; then
    echo "Kaggle CLI not found in venv. Installing..."
    pip install kaggle
fi

echo "Pushing notebook to Kaggle..."
# We push the kaggle_submission folder, explicitly requesting a T4 GPU accelerator
kaggle kernels push -p kaggle_submission --accelerator NvidiaTeslaT4

if [ $? -eq 0 ]; then
    echo "✅ Successfully pushed to Kaggle!"
    echo "You can view it in your Kaggle Notebooks: https://www.kaggle.com/"
else
    echo "❌ Failed to push. Did you set up ~/.kaggle/kaggle.json and accept the Gemma 2 license?"
fi
