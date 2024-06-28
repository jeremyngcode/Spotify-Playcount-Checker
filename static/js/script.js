const sortStates = ['unsorted', 'descending', 'ascending'];
const tables = document.querySelectorAll('table');

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
