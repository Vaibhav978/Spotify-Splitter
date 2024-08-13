console.log("splitter.js is loaded");

$(document).ready(function() {
    $('#homeButtonSplitter').css('opacity', 0).fadeTo(1000, 1); // Fade in over 1 second
    $('#updateTracksButton').css('opacity', 0).fadeTo(1000, 1);
    $('#fetchTracksButton').css('opacity', 0).fadeTo(1000, 1); // Ensure the container fades in

    const numDropdown = $('#num_albums');
    for (let i = 1; i <= 50; i++) {
        numDropdown.append($('<option>', {
            value: i,
            text: i
        }));
    }
    $('#fadeButton').prop('disabled', true);

    // Initially disable the split button
    $("#splitPlaylistButton").prop("disabled", true);

    // Load the Spotify API token from localStorage
    const token = localStorage.getItem("spotifyToken");

    // Check if the token exists
    if (token) {
        console.log("Spotify token found:", token);
    } else {
        console.log("Spotify token not found.");
    }

    // Function to enable/disable the split button
    function updateSplitButtonState() {
        const allTracksVisible = $(".track").length === $("#tracks_container .track:visible").length;
        if (allTracksVisible) {
            $("#splitPlaylistButton").prop("disabled", false);
        } else {
            $("#splitPlaylistButton").prop("disabled", true);
        }
    }

    // Function to load playlist tracks from Spotify
    function loadPlaylistTracks(playlistId) {
        $.ajax({
            url: `https://api.spotify.com/v1/playlists/${playlistId}/tracks`,
            type: "GET",
            headers: {
                Authorization: `Bearer ${token}`
            },
            success: function (response) {
                const tracksContainer = $("#tracks_container");
                tracksContainer.empty();
                response.items.forEach(item => {
                    const track = item.track;
                    const trackElement = $(`
                        <div class="track">
                            <h4>${track.name}</h4>
                            <p>${track.artists.map(artist => artist.name).join(", ")}</p>
                        </div>
                    `);
                    tracksContainer.append(trackElement);
                });
                // Show the split button after loading tracks
                $("#splitPlaylistButton").show();
                updateSplitButtonState();
            },
            error: function (xhr, status, error) {
                console.error("Failed to load playlist tracks:", error);
            }
        });
    }

    // Example usage
    const examplePlaylistId = "37i9dQZF1DXcBWIGoYBM5M"; // Replace with a valid playlist ID
    loadPlaylistTracks(examplePlaylistId);

    // Event handler for the split button
    $("#splitPlaylistButton").click(function () {
        console.log("Split playlist button clicked!");
        // Implement your split playlist logic here
    });
});

function submitAlbum() {
    console.log("Button clicked, fetching tracks...");

    fetch('/gettracks')
        .then(response => {
            console.log("Received response:", response);
            return response.json();
        })
        .then(data => {
            console.log("Received data:", data);
            displayTracks(data);
        })
        .catch(error => console.error('Error fetching tracks:', error));
}

function updateTracks() {
    const container = document.getElementById('tracks_container');
    container.innerHTML = '';  // Clear existing content

    // Make the fadeButton, num_albums, and tracks_container invisible and disable them
    hideElementsWhenGettingInformation()

    fetch('/updatetracks')
        .then(response => {
            console.log(response.json)
            return response.json();
        })
        .then(data => {
            console.log(data)
            displayTracks(data);
        })
        .catch(error => console.error('Error fetching tracks:', error));
}

function displayPlaylists(playlists) {
    console.log("DATA");
    console.log(playlists);
    const container = document.getElementById('tracks_container');
    hideElementsWhenGettingInformation();

    container.innerHTML = '';  // Clear existing content

    const columnsContainer = document.createElement('div');
    columnsContainer.className = 'columns-container';
    console.log(Object.keys(playlists));
    const clusterKeys = Object.keys(playlists);
    let currentRow;

    clusterKeys.forEach((clusterKey, index) => {
        if (index % 2 === 0) {
            currentRow = document.createElement('div');
            currentRow.className = 'playlist-row';
            columnsContainer.appendChild(currentRow);
        }

        const cluster = playlists[clusterKey];
        const clusterContainer = document.createElement('div');
        clusterContainer.className = 'playlist-container';

        const header = document.createElement('h4');
        header.textContent = `Playlist ${parseInt(clusterKey) + 1}: ${cluster.length} tracks`;
        clusterContainer.appendChild(header);

        const button = document.createElement('button');
        button.textContent = 'Add Playlist to Spotify Account';
        button.setAttribute('data-cluster', clusterKey); // Add data attribute
        clusterContainer.appendChild(button);

        const dropdown = document.createElement('select');
        dropdown.className = 'track-dropdown';
        dropdown.setAttribute('multiple', 'multiple');

        cluster.forEach(track => {
            const option = document.createElement('option');
            option.textContent = `${track.name} - ${track.artists.join(', ')}`;
            dropdown.appendChild(option);
        });

        clusterContainer.appendChild(dropdown);
        currentRow.appendChild(clusterContainer);
    });

    container.appendChild(columnsContainer);
    $('#fadeButton').css('opacity', 0).fadeTo(1000, 1); // Fade in over 1 second
    $('#tracks_container').css('opacity', 0).fadeTo(1000, 1); // Ensure the container fades in
    $('#fadeButton').prop('disabled', false);

    // Attach event listeners to buttons
    const buttons = document.querySelectorAll('.playlist-container button');
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            const clusterNumber = this.getAttribute('data-cluster');
            console.log(`Button for cluster ${clusterNumber} clicked`);
            // Call your function with the cluster number
            console.log(playlists[clusterNumber])

            showModal(clusterNumber, playlists);
        });
    });
}

// Your function to be called with the cluster number
function showModal(clusterNumber, playlists) {
    $('#overlay').removeClass('hidden-splitter').addClass('show');
    $('#playlistName').val('');
    $('#confirmButton').off('click').on('click', function() {
        const playlistName = $('#playlistName').val();
        console.log(`Confirmed playlist name: ${playlistName} for cluster ${clusterNumber}`);
        createPlaylistFromCluster(playlistName, clusterNumber, playlists);
    
        hideModal();
        // Add additional functionality for confirming the playlist name here
        });
    
        $('#cancelButton').off('click').on('click', function() {
            hideModal();
        });
    }
    
    function createPlaylistFromCluster(playlistName, clusterNumber, clustersData) {
        const url = '/createplaylist';
    
        // Prepare the data to send
        const data = {
            "playlistName": playlistName,
            "clusterNumber": clusterNumber,
            "clusters": clustersData
        };
    
        // Make the POST request using fetch
        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                console.log('Success:', result);
                const { playlistId, token } = result;
                console.log(`Playlist ID: ${playlistId}, Token: ${token}`);
                // Call the function to add tracks to this new playlist using the obtained playlistId and token
                const cluster = clustersData[clusterNumber];
                const trackUris = cluster.map(track => `spotify:track:${track.id}`);
                addTracksToPlaylist(playlistId, trackUris, token);
            } else {
                console.error('Error:', result.error);
            }
        })
        .catch(error => console.error('Error:', error));
    }
    
    function addTracksToPlaylist(playlistId, trackUris, token) {
        console.log(playlistId)
        const batchSize = 90;
        const urlTemplate = `https://api.spotify.com/v1/playlists/${playlistId}/tracks`;
    
        for (let i = 0; i < trackUris.length; i += batchSize) {
            const batch = trackUris.slice(i, i + batchSize);
    
            fetch(urlTemplate, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ uris: batch })
            })
            .then(response => response.json())
            .then(result => {
                if (result.snapshot_id) {
                    console.log('Batch added successfully:', result);
                } else {
                    console.error('Error adding batch:', result);
                }
            })
            .catch(error => console.error('Error:', error));
        }
    }
    
    function hideModal() {
        $('#overlay').removeClass('show').addClass('hidden-splitter');
    }
    
    function getSplitPlaylists() {
        fetch('/splittracks')
        .then(response => response.json())
        .then(data => displayPlaylists(data)) // Call displayPlaylists directly
        .catch(error => console.error('Error fetching tracks:', error));
    }
    
    function hideElementsWhenGettingInformation() {
        $('#artist_name, #searchResults, #submitButton').css('opacity', 0).fadeTo(0, 0);
        $('#fadeButton').prop('disabled', true);
    }
    
    function displayTracks(data) {
        console.log(data);
    
        const container = document.getElementById('tracks_container');
        container.innerHTML = '';  // Clear existing content
        if (data.error) {
            const message = document.createElement('h3');
            message.textContent = data.error;
            container.appendChild(message);
        } else if (!data.tracks || data.tracks.length === 0) {  // Check if tracks are empty
            const message = document.createElement('h3');
            message.textContent = "No tracks found";
            container.appendChild(message);
        } else {
            const tracks = data.tracks;
            const header = document.createElement('h3');
            header.textContent = `Obtained ${tracks.length} saved tracks`;
            container.appendChild(header);
    
            const columnsContainer = document.createElement('div');
            columnsContainer.className = 'columns-container';
    
            // Set the number of columns to 3
            const numColumns = 3;
            const tracksPerColumn = Math.ceil(tracks.length / numColumns);
    
            for (let i = 0; i < numColumns; i++) {
                const columnElement = document.createElement('div');
                columnElement.className = 'track-column';
    
                const start = i * tracksPerColumn;
                const end = Math.min(start + tracksPerColumn, tracks.length);
    
                for (let j = start; j < end; j++) {
                    const track = tracks[j];
                    const trackElement = document.createElement('div');
                    trackElement.className = 'track';
    
                    const trackInfo = document.createElement('p');
                    trackInfo.textContent = `${j + 1}. ${track.name} - ${track.artists.join(', ')}`;
    
                    trackElement.appendChild(trackInfo);
                    columnElement.appendChild(trackElement);
                }
    
                columnsContainer.appendChild(columnElement);
            }
    
            container.appendChild(columnsContainer);
            $('#fadeButton').css('opacity', 0).fadeTo(1000, 1); // Fade in over 1 second
            $('#tracks_container').css('opacity', 0).fadeTo(1000, 1); // Ensure the container fades in
            $('#fadeButton').prop('disabled', false);
        }
    }
    
