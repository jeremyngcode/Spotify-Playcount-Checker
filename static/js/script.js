const tables = document.querySelectorAll('table');

// Table sorting
const sortStates = ['unsorted', 'descending', 'ascending'];

tables.forEach((table) => {
	let playcountHeader = [
			table.querySelector('th.playcount span'),
			table.querySelector('th.playcount').cellIndex,
			table.querySelector('th.playcount').classList
		];
	let popularityHeader = [
			table.querySelector('th.popularity span'),
			table.querySelector('th.popularity').cellIndex,
			table.querySelector('th.popularity').classList
		];
	let headers = [playcountHeader, popularityHeader];

	let unsortedRows = Array.from(table.tBodies[0].rows);

	headers.forEach(([header, colIdx, headerClassList], index) => {
		header.onclick = (event) => {
			let rows = Array.from(unsortedRows);
			let sortedRows;

			if (headerClassList.contains(sortStates[0])) {
				headerClassList.replace(sortStates[0], sortStates[1]);
				sortedRows = rows.sort((a, b) => {
					let aText = a.cells[colIdx].innerText.replaceAll(',', '');
					let bText = b.cells[colIdx].innerText.replaceAll(',', '');
					return Number(bText) - Number(aText);
				});
			} else if (headerClassList.contains(sortStates[1])) {
				headerClassList.replace(sortStates[1], sortStates[2]);
				sortedRows = rows.sort((a, b) => {
					let aText = a.cells[colIdx].innerText.replaceAll(',', '');
					let bText = b.cells[colIdx].innerText.replaceAll(',', '');
					return Number(aText) - Number(bText);
				});
			} else if (headerClassList.contains(sortStates[2])) {
				headerClassList.replace(sortStates[2], sortStates[0]);
				sortedRows = rows;
			};

			sortedRows.forEach((row) => {
				table.tBodies[0].appendChild(row);
			});

			headers.forEach(([, , headerClassList2], index2) => {
				if (index2 !== index) {
					headerClassList2.remove(...sortStates);
					headerClassList2.add(sortStates[0]);
				};
			});
		};
	});
});

// Loading animation (form submission)
let loader;
const searchForm = document.querySelector('.spotify-uri-search-form');

searchForm.onsubmit = (event) => {
	loader = searchForm.querySelector('.loader');
	loader.classList.add('loading');
};

// Loading animation (links)
let loader2 = document.querySelector('.loader-2');
const artistLinksCard = document.querySelector('.artist-links-card');

if (artistLinksCard) {
	let albumArtists = artistLinksCard.querySelectorAll('.name');

	albumArtists.forEach((artist) => {
		artist.onclick = (event) => {
			loader2.classList.add('loading-2');
		};
	});
} else {
	tables.forEach((table) => {
		let titleColumn = Array.from(table.querySelectorAll('.title'));
		titleColumn = titleColumn.slice(1);

		for (let cell of titleColumn) {
			let name = cell.querySelector('.name');
			let artists = cell.querySelectorAll('.artist');

			if (name) {
				name.onclick = (event) => {
					loader2.classList.add('loading-2');
				};
			};
			if (artists) {
				artists.forEach((artist) => {
					artist.onclick = (event) => {
						loader2.classList.add('loading-2');
					};
				});
			};
		};
	});
};
