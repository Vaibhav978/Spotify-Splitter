console.log("splitter.js is loaded");

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

function displayTracks(tracks) {
    const container = document.getElementById('tracks-container');
    container.innerHTML = '';  // Clear existing content

    tracks.forEach(track => {
        const trackElement = document.createElement('div');
        trackElement.className = 'track';

        const trackName = document.createElement('h3');
        trackName.textContent = track.name;
        
        const artistNames = document.createElement('p');
        artistNames.textContent = 'Artists: ' + track.artists.join(', ');

        trackElement.appendChild(trackName);
        trackElement.appendChild(artistNames);

        container.appendChild(trackElement);
    });
}
