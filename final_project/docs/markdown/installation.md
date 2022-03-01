# SpaceTime Query Reduction Example

Check out the Repo linke here: [Repo Link](https://github.com/csci-e-29/2021sp-final-project-svideloc-1)

Also, check out my presentation here: [Final Presentation](https://www.canva.com/design/DAEc3PrpSHc/VGWTfQ6WDJ_srOLB5FH8BQ/view?utm_content=DAEc3PrpSHc&utm_campaign=designshare&utm_medium=link&utm_source=sharebutton)

## Instructions to Run Code

Keep in mind I am only sharing some of my code, I discuss some other parts of the project, but I at least wanted to share the main part of the code with the class, the sphinx docs has more details!

I have a test csv file saved in data/test_files.csv. This is so that you may experiement with running the code yourself

```sh
git clone https://github.com/csci-e-29/2021sp-final-project-svideloc-1.git
cd 2021sp-final-project-svideloc-1
pipenv install
pipenv shell
```

To see the available arguments of the python script run
```sh
python -m final_project -h
```

Run an example with:
```sh
python -m final_project --f data/test_file.csv --lat=1 --lon=2 --time=3 --name=4 -n job_name -j "justification is here" -t 900 -d 100
```

This should take about 30 seconds on the dataset of 5000 points and output a csv and a kml file with the updated queries which should be of length 3146 with the above parametesr. This example is ran using adsb flight data, so it is not entirely representative of the real data that is run through this algorithm. Typically we see much greater decreases in the total number of queries, but this is just a demo!

## Contact Information

Sam Videlock

svideloc@gmail.com