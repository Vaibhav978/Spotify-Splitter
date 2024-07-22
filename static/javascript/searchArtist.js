$(document).ready(function() {
    // Populate the dropdown with numbers from 1 to 20
    var numDropdown = $('#num_albums');
    for (var i = 1; i <= 20; i++) {
        numDropdown.append($('<option>', {
            value: i,
            text: i
        }));
    }

    // Fade in elements with delay
    setTimeout(function() {
        $('#displayName').addClass('fade-in');
        $('#instructions').addClass('fade-in');
        $('#homeButton').addClass('fade-in');
        $('#artistLabel').addClass('fade-in');
        $('#artist_name').addClass('fade-in');
        $('#albumCountLabel').addClass('fade-in');
        $('#num_albums').addClass('fade-in');
        $('#submitButton').addClass('fade-in');
    }, 100);

    // Handle form submission asynchronously
    $('#searchArtist').submit(function(event) {
        event.preventDefault();  // Prevent default form submission

        var artistName = $('#artist_name').val();
        var numAlbums = $('#num_albums').val(); // Get the selected number of albums

        $.ajax({
            type: 'POST',
            url: '/search_artist',
            contentType: 'application/json',
            data: JSON.stringify({ 'artist_name': artistName, 'num_albums': numAlbums }),
            success: function(response) {
                displayAlbums(response, artistName, numAlbums);
            },
            error: function(error) {
                console.error('Error:', error);
            }
        });
    });
});

function displayAlbums(albums, artist_name, num_albums) {
    var searchResults = $('#searchResults');
    searchResults.empty();  // Clear previous results
    var heading = $('<h2>').text('Top ' + num_albums + ' Albums by ' + artist_name);
    searchResults.append(heading);
    albums.forEach(function(album, index) {
        var albumElement = $('<div>').addClass('album').text((index + 1) + '. ' + album.name);
        searchResults.append(albumElement);
    });

    $('#searchResults').addClass('fade-in');
}
