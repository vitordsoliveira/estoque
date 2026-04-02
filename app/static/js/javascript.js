function normalizeSearchText(value) {
	return (value || '')
		.normalize('NFD')
		.replace(/[\u0300-\u036f]/g, '')
		.toLowerCase()
		.trim();
}

function createEmptyStateRow(tableBody, columnCount, message) {
	const emptyRow = document.createElement('tr');
	emptyRow.setAttribute('data-search-empty-row', 'true');
	emptyRow.style.display = 'none';

	const emptyCell = document.createElement('td');
	emptyCell.colSpan = columnCount;
	emptyCell.style.textAlign = 'center';
	emptyCell.style.padding = '20px';
	emptyCell.textContent = message;

	emptyRow.appendChild(emptyCell);
	tableBody.appendChild(emptyRow);

	return emptyRow;
}

document.addEventListener('DOMContentLoaded', () => {
	const searchInputs = document.querySelectorAll('[data-table-search]');

	searchInputs.forEach((searchInput) => {
		const tableSelector = searchInput.dataset.tableTarget;
		const table = document.querySelector(tableSelector);

		if (!table || !table.tBodies.length) {
			return;
		}

		const tableBody = table.tBodies[0];
		const searchableRows = Array.from(tableBody.querySelectorAll('tr[data-searchable-row]'));

		if (!searchableRows.length) {
			return;
		}

		const filterSelector = searchInput.dataset.filterTarget;
		const filterElement = filterSelector ? document.querySelector(filterSelector) : null;
		const filterKey = searchInput.dataset.filterKey || '';
		const columnCount = table.querySelectorAll('thead th').length || 1;
		const emptyMessage = searchInput.dataset.emptyMessage || 'Nenhum resultado encontrado.';
		const emptyRow = createEmptyStateRow(tableBody, columnCount, emptyMessage);

		const applyFilters = () => {
			const query = normalizeSearchText(searchInput.value);
			const filterValue = filterElement ? String(filterElement.value || '') : '';
			let visibleCount = 0;

			searchableRows.forEach((row) => {
				const rowText = normalizeSearchText(row.dataset.searchText || row.textContent);
				const matchesText = !query || rowText.includes(query);
				const rowFilterValue = filterKey ? String(row.dataset[filterKey] || '') : '';
				const matchesFilter = !filterElement || !filterValue || rowFilterValue === filterValue;
				const isVisible = matchesText && matchesFilter;

				row.style.display = isVisible ? '' : 'none';
				if (isVisible) {
					visibleCount += 1;
				}
			});

			emptyRow.style.display = visibleCount === 0 ? '' : 'none';
		};

		searchInput.addEventListener('input', applyFilters);
		if (filterElement) {
			filterElement.addEventListener('change', applyFilters);
		}

		applyFilters();
	});
});
