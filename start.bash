# Check if app/app.py exists
if [ ! -f "app/app.py" ]; then
    echo "app/app.py not found. Please make sure it exists in the current directory."
    exit 1
fi
# Run the app/app.py script
python app/app.py


echo "Bot started..."