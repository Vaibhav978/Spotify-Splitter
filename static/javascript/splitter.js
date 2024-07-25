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
    $('#fadeButton, #num_albums').prop('disabled', true);
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
        header.textContent = `Playlist ${parseInt(clusterKey) + 1}`;
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
    $('#num_albums').css('opacity', 0).fadeTo(1000, 1);
    $('#tracks_container').css('opacity', 0).fadeTo(1000, 1); // Ensure the container fades in
    $('#fadeButton, #num_albums').prop('disabled', false);

    // Attach event listeners to buttons
    const buttons = document.querySelectorAll('.playlist-container button');
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            const clusterNumber = this.getAttribute('data-cluster');
            console.log(`Button for cluster ${clusterNumber} clicked`);
            // Call your function with the cluster number
            yourFunction(clusterNumber);
        });
    });
}

// Your function to be called with the cluster number
function yourFunction(clusterNumber) {
    console.log(`Function called with cluster number: ${clusterNumber}`);
    // Add your functionality here
}



function getSplitPlaylists() {
    fetch('/splittracks')
    .then(response => response.json())
    .then(data => displayPlaylists(data)) // Call displayPlaylists directly
    .catch(error => console.error('Error fetching tracks:', error));
}


function hideElementsWhenGettingInformation(){
    $('#artist_name, #searchResults, #submitButton, #num_albums').css('opacity',0).fadeTo(0,0);
    $('#fadeButton, #num_albums').prop('disabled', true);
}


function displayTracks(data) {
    console.log(data);

    const container = document.getElementById('tracks_container');
    container.innerHTML = '';  // Clear existing content
    if (data.error) {
        const message = document.createElement('h3');
        message.textContent = data.error;
        container.appendChild(message);
    }
    else{
    tracks = data.tracks
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
    $('#num_albums').css('opacity', 0).fadeTo(1000, 1);
    $('#tracks_container').css('opacity', 0).fadeTo(1000, 1); // Ensure the container fades in
    $('#fadeButton, #num_albums').prop('disabled', false);
}
}

