# metadata.tvshows.thesportsdb.python
Python version of the Kodi scraper for Sports events for Kodi 20 (Nexus) and later

## File Naming
File have to be named in a format Kodi recognizes as a TV Show episode and in a way that will uniquely identify them.  For more specific information on file naming, please see:

[https://kodi.wiki/view/Naming_video_files/Episodes#Single_Episode_Files](https://kodi.wiki/view/Naming_video_files/Episodes#Single_Episode_Files)

There are three options:

### Using Season/Episode Numbers
Kodi reconizes files with the `SxxExx` format.  The season has to be a number, so for seasons on The SportsDB that are multi-year (i.e. 2020-2021) use the first year.  The SportsDB doesn't provide episode numbers, so the scraper numbers each event in a season as it loads them.  To find the episode number you'll have to count from the first game in the season (starting at 1).  The file name can contain any other information you want, but Kodi will only match on the season and epsiode number.  For example:

`NFL.S2021E02.Atlanta.Falcons.vs.Philadelphia.Eagles.mp4`

### Using Dates
Kodi recognizes files that have the date in a few specific formats.  You can only use this option if the sport only has one game on a given day.  For example:

`Formula.1.2022-03-20.Bahrain.Grand.Prix.mp4`

### Using Game Name
Starting with Kodi 20 (Nexus), Kodi will use the filename to try and match the title of an epsiode if the name ends with `.special` before the file extension.  Because this is most likely to be used for sports that have multiple games in a day and teams could play each other multiple times, you need to include the date.  But it needs to be numbers only, or Kodi will use the date matching above, which will cause problems.  In this case the entire file name is used as a match, so it must be in the format of `<league>.<date>.<name>.special.ext`.  For example:

`English Premier League.20210813.Brentford.vs.Arsenal.special.mp4`

Kodi will do fuzzy searching, so you can use periods or underscores instead of spaces, although you should still separate the items with a period.  Whens scraper, Kodi will only display the actual game name (i.e. Brentford vs Arsenal).  The rest of the file is just used for matching purposes. 

## Parsing NFO Files for Leagues
This scraper does support parsing nfo files to identify a league even if the folder name does not match the league name.  For more specific information on parsing nfo files, please see:

[https://kodi.wiki/view/NFO_files/Parsing](https://kodi.wiki/view/NFO_files/Parsing)

The SportsDB TV Show scraper uses the URL for the league page as the parsing URL.  So, for instance, the parsing URL for MLS (American Major League Soccer) would be:

`https://www.thesportsdb.com/league/4346-American-Major-League-Soccer`

or

`https://www.thesportsdb.com/league/4346`

