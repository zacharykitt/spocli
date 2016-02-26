# Spocli
A command-line interface for interacting with the Spotify API and (for linux) the desktop application.

---

## Commands

### Artists

* list artist albums: `artists --e(ndpoint) albums --i(d) <artist_id>`
* list related artists: `artists --e(ndpoint) related --i(d) <artist_id>`

### Browse

* list featured playlists: `browse --e(ndpoint) featured-playlists`
* list all categories: `browse --e(ndpoint) categories`
* list a category's playlists: `browse --e(ndpoint) list-playlists --i(d) <category_id>`
* list new album releases: `browse --e(ndpoint) new-releases`


### Search

* search resources by term: `search --t(ype) [artist, album, track] --q(uery) '<term>'`

### Player (linux only)

* play player: `player --c(ommand) play`
* pause player: `player --c(ommand) pause`
* stop player: `player --c(ommand) stop`
* next song: `player --c(ommand) next`
* previous song: `player --c(ommand) prev`
* open a specific item: `player --c(ommand) open --u(ri) <item_uri>`
* list track info: `player --c(ommand) info`

---

## Future Dev Plans

* update the new-releases function to output album artist information
* improve linux player support by adding error-handling
* expand player support for osx and windows
* allow for program persistence so item id and uris can be passed to other functions more easily