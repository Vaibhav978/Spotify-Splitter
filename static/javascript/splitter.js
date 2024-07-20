console.log("splitter.js is loaded");
const hasReceivedTracks = false
$(document).ready(function() {
    $('#homeButtonSplitter').css('opacity', 0).fadeTo(1000, 1); // Fade in over 1 second
    $('#updateTracksButton').css('opacity', 0).fadeTo(1000, 1);
    $('#fetchTracksButton').css('opacity', 0).fadeTo(1000, 1); // Ensure the container fades in\
    
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

function updateTracks(){
    fetch('/updatetracks')
        .then(response => {
            return response.json();
        })
        .then(data => {
            displayTracks(data)
        })
        .catch(error => console.error('Error fetching tracks:', error));
    
}

function getSplitPlaylists() {
    fetch('/splittracks')
}

function displayTracks(data) {
    const tracks = data.tracks
    
    const container = document.getElementById('tracks_container');
    container.innerHTML = '';  // Clear existing content

    const header = document.createElement('h3');
    header.textContent = `Obtained ${tracks.length} saved tracks`;
    container.appendChild(header);

    const tracksPerColumn = 200;
    const numColumns = Math.ceil(tracks.length / tracksPerColumn);

    const columnsContainer = document.createElement('div');
    columnsContainer.className = 'columns-container';

    for (let i = 0; i < numColumns; i++) {
        const columnElement = document.createElement('div');
        columnElement.className = 'track-column';

        const start = i * tracksPerColumn;
        const end = Math.min(start + tracksPerColumn, tracks.length);

        for (let j = start; j < end; j++) {
            const track = tracks[j];
            const trackElement = document.createElement('div');
            trackElement.className = 'track';

            const trackIndex = document.createElement('span');
            trackIndex.className = 'track-index';
            trackIndex.textContent = `${j + 1}. `; // Display index starting from 1

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
    $('#tracks_container').css('opacity', 0).fadeTo(1000, 1); // Ensure the container fades in\
    $('#fadeButton, #num_albums').prop('disabled', false);
}
