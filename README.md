Spotify Playcount Checker
=========================

Intro
-----
I had created a personal [dashboard for Spotify artists](https://github.com/jeremyngcode/Spotify-Graphs-Dashboard) for visualizing streams and listeners data from their Spotify provided CSV file. Now I wanted to also create a simple and friendly UI for retrieving playcount / popularity data from Spotify's web API for fun, so here it is!

As usual, I'm using my favourite theme colours of purple and orange again. 😁

The App / Usage
---------------
Run [app.py](app.py) and then type in the Spotify URI or URL of the resource you're looking for in the search field as per the formatting [here](https://developer.spotify.com/documentation/web-api/concepts/spotify-uris-ids). The search string for a URI should look something like this: `spotify:artist:22characters-long-here`

Inputting a wrongly formatted or invalid Spotify URI / URL will result in a mischievous cheeky pokemon appearing, don't try it! <br>

The app is currently able to fetch data for 3 categories of which one of two page types will be served depending on the category as per below.

1. Artist page ([playcount-artist.html.j2](playcount-artist.html.j2)) for <em>Artist</em> queries. <br>
   <img src="https://github.com/jeremyngcode/Spotify-Playcount-Checker/assets/156220343/c2ec97a3-5b4e-4994-8ebf-e4c32b27c990" alt="sample-artist-page" width="600">

2. Album page ([playcount-album.html.j2](playcount-album.html.j2)) for <em>Album</em> and <em>Track</em> queries. <br>
   <img src="https://github.com/jeremyngcode/Spotify-Playcount-Checker/assets/156220343/a31b9a9d-9f25-4aa8-93a9-999a663ad07b" alt="sample-album-page" width="600">

   For track queries, the corresponding table row will be highlighted as well, as seen in the screenshot above.

All Spotify icon and image hyperlinks will redirect to Spotify's site, while text hyperlinks are internal, most of which are simply new queries. Pressing the A, C, and S navigation buttons at the bottom right corner will scroll to the Albums, Compilations, and Singles tables respectively.

Do note that it is possible a timeout error may occur if Spotify takes too long to respond to any one API call that the app makes. It isn't common from my testing, simply retry and it should work again. So far I've only experienced this with very large artist catalogs.

Some Thoughts...
----------------
While the app is fast for album and track queries, it does however take some time for artist ones. As a rough gauge, my own artist page with about 30+ releases takes on average ~4 seconds. Unfortunately I'm not aware of a method / endpoint for retrieving playcount data for multiple releases in one call at this point, and playcount data in particular is actually not officially documented on Spotify's developer site. Nevertheless, while I was trying to find ways to speed things up, I did learn to use the `Session` object from the `requests` library for the first time at the very least! And it did actually make a very noticeable difference.

Another first for me was dark mode styling which I spent quite a bit of time and turned out to be quite satisfying! Instead of using a toggle for this, I made it based on the browser appearance settings with the `@media (prefers-color-scheme: dark)` CSS rule which I think is simpler.

#### Notable libraries used / learned for this project:
- [Flask](https://pypi.org/project/Flask/)
- [Jinja](https://pypi.org/project/Jinja2/)
- [requests](https://pypi.org/project/requests/)

---

![sample-album-page-dark](https://github.com/jeremyngcode/Spotify-Playcount-Checker/assets/156220343/26720a89-ed4c-4f2d-b725-af36bcb44c69)
