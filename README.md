Spotify Playcount Checker
=========================

Intro
-----
I had created a personal [dashboard for Spotify artists](https://github.com/jeremyngcode/Spotify-Graphs-Dashboard) for visualizing streams and listeners data from their Spotify provided CSV file. Now I wanted to also create a simple and friendly UI for retrieving playcount / popularity data from Spotify's web API!

I'm aware that playcount data for each individual track is already openly available on Spotify desktop, but perhaps summing up album and artist playcount as well might be useful for some. You will also be able to get an overview of the total playcount for each release by an artist on one page with popularity scores being displayed alongside. Regardless, building this app was somewhat for fun too, so here it is anyway!

As usual, I'm using my favourite theme colours of purple and orange again. 😁

The App / Usage
---------------
Run [app.py](app.py) and then copy-paste the Spotify URI or URL of the resource you're looking for into the search field as per the formatting [here](https://developer.spotify.com/documentation/web-api/concepts/spotify-uris-ids). The search string for a URI should look something like this: `spotify:artist:22characters-long-here`

Inputting a wrongly formatted or invalid Spotify URI / URL will result in a mischievous cheeky pokemon appearing, don't try it! <br>

The app is currently able to fetch data for 4 categories of which one of three page types will be served depending on the category as per below.

1. Artist page ([playcount-artist.html.j2](templates/playcount-artist.html.j2)) for <em>Artist</em> queries. <br>
   <img src="https://github.com/jeremyngcode/Spotify-Playcount-Checker/assets/156220343/d841fee7-eee3-4d46-b822-26a73a42610a" alt="sample-artist-page-light" width="600">

2. Album page ([playcount-album.html.j2](templates/playcount-album.html.j2)) for <em>Album</em> and <em>Track</em> queries. <br>
   <img src="https://github.com/jeremyngcode/Spotify-Playcount-Checker/assets/156220343/d10e8346-0c86-40c9-8829-a99d7702bafc" alt="sample-album-page-light" width="600">

   For track queries, the corresponding table row will be highlighted as well, as seen in the screenshot above.

3. Playlist page ([playcount-playlist.html.j2](templates/playcount-playlist.html.j2)) for <em>Playlist</em> queries. <br>
   <img src="https://github.com/jeremyngcode/Spotify-Playcount-Checker/assets/156220343/492dc319-4989-4910-b63f-c256f15f977b" alt="sample-playlist-page-light" width="600">

- All Spotify icon and image hyperlinks will redirect to Spotify's site, while text hyperlinks are internal, most of which are simply new queries. Pressing the A, C, and S navigation buttons at the bottom right corner will scroll to the Albums, Compilations, and Singles tables respectively.

- Do note that it is possible a timeout error may occur if Spotify takes too long to respond to any one API call that the app makes. It isn't common from my testing, simply retry and it should work again. So far I've only experienced this with very large artist catalogs.

- Any track that has not accumulated at least 1000 streams will show a playcount value of 0. Not sure why, ask Spotify.

- In case of interest, a JSON file (spotify-data.json) with all the relevant Spotify data that were passed on to the frontend from the last query is kept.

Some Thoughts...
----------------
While the app is fast for album and track queries, it does however take some time for artist and playlist ones. As a rough gauge, my own artist page with about 30+ releases takes on average ~4 seconds. Unfortunately I'm not aware of a method / endpoint for retrieving playcount data for multiple releases in one call at this point, and playcount data in particular is actually not officially documented on Spotify's developer site. Nevertheless, while I was trying to find ways to speed things up, I did learn to use the `Session` object from the `requests` library for the first time at the very least! And it did actually make a very noticeable difference.

Another first for me was dark mode styling which I spent quite a bit of time working on and turned out to be quite satisfying! Instead of using a toggle for this, I made it based on the browser appearance settings with the `@media (prefers-color-scheme: dark)` CSS rule which I think is simpler.

#### Notable libraries used / learned for this project:
- [Flask](https://pypi.org/project/Flask/)
- [Jinja](https://pypi.org/project/Jinja2/)
- [requests](https://pypi.org/project/requests/)

---

![sample-album-page-dark](https://github.com/jeremyngcode/Spotify-Playcount-Checker/assets/156220343/7283d015-59d1-4387-a8e6-d0e7bd16e13f)
