# Gamma Map


- [ ] Default the single expiry gamma map to the expiration date that's either today or if it's a weekend, then the next valid expiration date
- [x] Instead of a checkbox for including the ODTE options, make it an actual toggle
- [x] Only the SPXW options seem to be calculating correctly
- [x]the graphs are too wide on the screen, let's add some margin or something to make them more readable. Maybe can we add the controls to the left of the graph and have the graph on the right. That would make the grpah less wide.
- [x] We need to see more ticks on the graphs, at least every 50, maybe every 25
- [x] We need to filter the expirations to avoid weekends, for example 4-18-2026 is a saturday
- [x] Let's remove the call wall and put wall metrics
- [x] write some unit tests around the loading of the options files to ensure it working correctly and getting all the relevant options files for the aggregate, i.e. the most recent sample of an expiration
- [x] Is there anyway with streamlit and plotly to auto refresh the charts? The spot on the gamma charts seems cached at a level that's not current
- [x] Let's default the single expiry selected to the most recent date and then the dropdown should have the dates in descending order