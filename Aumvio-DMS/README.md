## Installation
Make sure to install Qt platform library
> sudo apt-get install libxcb-xinerama0

Setup the conda environment
> conda create -n dms-demo python=3.9
> conda activate dms-demo
> conda install pip
> pip install -r requirements.txt

## How to Run

Check installation of Clip module
> python check.py

Run the DMS system
> python DMS.py

# GUI Modification

The overall window size is defined in `ui_driver.py`:

```python
    def setupUi(self, Form):
        r = 1.2 # 1.2
        self.ratio = r
        Form.setObjectName("Form")
        Form.resize(896 * r, 620 * r)
```

To switch to full screen, change the `driver.MainWindow.show()` in main function of `DMS.py` to `driver.MainWindow.showFullScreen()`.

To modify positions of elements, change the coordinates in `ui_driver.py`'s `QRect()`. All 1st arguments of `QRect()` have been added 70 (shift horizontally to the right).
