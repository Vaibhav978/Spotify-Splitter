$(document).ready(function() {
    $('#searchArtist').submit(function(event) {
        event.preventDefault();  // Prevent default form submission

        var artistName = $('#artist_name').val();

        $.ajax({
            type: 'POST',
            url: '/search_artist',
            contentType: 'application/json',
            data: JSON.stringify({ 'artist_name': artistName }),
            success: function(response) {
                displayAlbums(response);
            },
            error: function(xhr, status, error) {
                console.error('Error:', error);
            }
        });
    });
});

function displayAlbums(albums) {
    var searchResults = $('#searchResults');
    searchResults.empty();  // Clear previous results

    albums.forEach(function(album) {
        var albumElement = $('<div>').addClass('album').text(album.name);
        searchResults.append(albumElement);
    });
}
