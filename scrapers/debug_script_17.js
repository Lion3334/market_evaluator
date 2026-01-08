

	var currentGemrateId = "";

	$('#pieWrapper, #popWrapper, #gemWrapper, #gradeWrapper, #psaWrapper, #beckettWrapper, #sgcWrapper, #cgcWrapper').hide();

	function gradeToFloat(grade) {
		return parseFloat(grade.replace('g', '').replace('_', '.'));
	}

	function generateAdvancedUrl(graderData, graderKey) {
		const grader = graderKey.toLowerCase();
		const year = graderData.year;
		let category = graderData.category;
		const set_name = encodeURIComponent(graderData.set_name);
		
		// Map grader names for URL
		const graderMap = {
			'psa': 'psa',
			'beckett': 'bgs',
			'bgs': 'bgs',
			'sgc': 'sgc',
			'cgc': 'cgc'
		};
		
		// CGC category mapping - default to 'tcg-cards' for non-sport categories, append '-cards' for sports
		if (grader === 'cgc') {
			const validCategories = ['baseball', 'football', 'basketball', 'soccer', 'hockey', 'multisport', 'wrestling', 'racing', 'mma', 'tennis', 'rugby', 'boxing', 'golf', 'cricket'];
			if (!validCategories.includes(category.toLowerCase())) {
				category = 'tcg-cards';
			} else {
				category = category.toLowerCase() + '-cards';
			}
		}
		
		const urlGrader = graderMap[grader] || grader;
		
		// PSA uses advanced URL structure, others use standard
		if (grader === 'psa') {
			// Map category to proper format for PSA URLs
			const card_category_map = {
				"tcg": "tcg-cards",
				"misc": "misc-cards",
				"boxing-wrestling-mma": "boxing-wrestling-cards-mma",
				"soccer": "soccer-cards",
				"golf": "golf-cards",
				"hockey": "hockey-cards",
				"baseball": "baseball-cards",
				"basketball": "basketball-cards",
				"multi-sport": "multi-sport-cards",
				"non-sport": "non-sport-cards",
				"football": "football-cards",
				"minor-league": "minor-league-cards"
			};
			// Use mapped category if it exists, otherwise keep original
			category = card_category_map[category.toLowerCase()] || category;
			return `https://www.gemrate.com/item-details-advanced?grader=${urlGrader}&year=${year}&category=${category}&set_name=${set_name}`;
		} else {
			return `https://www.gemrate.com/item-details?grader=${urlGrader}&year=${year}&category=${category}&set_name=${set_name}`;
		}
	}

	function roundUpToNearestTenPower(num) {
		if (num <= 0) return 0; // Handle negative or zero values

		let factor = Math.pow(10, Math.floor(Math.log10(num)));
		return Math.ceil(num / factor) * factor;
	}

	const graderColors = {
		'psa': '#EB1C2D',
		'beckett': '#54C4C8',
		'bgs': '#54C4C8',  
		'sgc': '#000000',
		'cgc': '#00B84F'
	};

	const gradingLists = {
		psa: ['auth','q1','g1','g1_5','q2','g2','g2_5','q3','g3','g3_5','q4','g4','g4_5','q5','g5','g5_5','q6','g6','g6_5','q7','g7','g7_5','q8','g8','g8_5','q9','g9','g10'],
		beckett: ['g1','g1_5','g2','g2_5','g3','g3_5','g4','g4_5','g5','g5_5','g6','g6_5','g7','g7_5','g8','g8_5','g9','g9_5','g10p','g10b'],
		sgc: ['ga','g1','g1_5','g2','g2_5','g3','g3_5','g4','g4_5','g5','g5_5','g6','g6_5','g7','g7_5','g8','g8_5','g9','g9_5','g10','g10p'],
		cgc: ['g1','g1_5','g2','g2_5','g3','g3_5','g4','g4_5','g5','g5_5','g6','g6_5','g7','g7_5','g8','g8_5','g9','g9_5','g10','g10pristine','g10perfect'],
	};

	let psa_grading_scale = {
		'g10': "Gem Mint 10",
		'g9': "Mint 9",
		'g8_5':  "NM-MT+ 8.5",
		'g8': "NM-MT 8",
		'g7_5': "NM+ 7.5",
		'g7': "NM 7",
		'g6_5': "EX-MT+ 6.5",
		'g6': "EX-MT 6",
		'g5_5': "EX+ 5.5",
		'g5': "EX 5",
		'g4_5': "VG-EX+ 4.5",
		'g4': "VG-EX 4",
		'g3_5': "VG+ 3.5",
		'g3': "VG 3",
		'g2_5': "GOOD+ 2.5",
		'g2': "GOOD 2",
		'g1_5': "FAIR 1.5",
		'g1': "POOR 1"
	};

	let beckett_grading_scale = {
		'g10b': "Pristine BL 10",
		'g10p': "Pristine 10",
		'g9_5': "Gem Mint 9.5",
		'g9': "Mint 9",
		'g8_5':  "NM-MT+ 8.5",
		'g8': "NM-MT 8",
		'g7_5': "NM+ 7.5",
		'g7': "NM 7",
		'g6_5': "EX-MT+ 6.5",
		'g6': "EX-MT 6",
		'g5_5': "EX+ 5.5",
		'g5': "EX 5",
		'g4_5': "VG-EX+ 4.5",
		'g4': "VG-EX 4",
		'g3_5': "VG+ 3.5",
		'g3': "VG 3",
		'g2_5': "GOOD+ 2.5",
		'g2': "GOOD 2",
		'g1_5': "FAIR 1.5",
		'g1': "POOR 1"
	};

	let sgc_grading_scale = {
		"g10p": "Pristine 10",
		"g10": "Gem Mint 10",
		"g9_5": "Mint+",
		'g9': "Mint 9",
		'g8_5':  "NM-MT+ 8.5",
		'g8': "NM-MT 8",
		'g7_5': "NM+ 7.5",
		'g7': "NM 7",
		'g6_5': "EX-MT+ 6.5",
		'g6': "EX-MT 6",
		'g5_5': "EX+ 5.5",
		'g5': "EX 5",
		'g4_5': "VG-EX+ 4.5",
		'g4': "VG-EX 4",
		'g3_5': "VG+ 3.5",
		'g3': "VG 3",
		'g2_5': "GOOD+ 2.5",
		'g2': "GOOD 2",
		'g1_5': "FAIR 1.5",
		'g1': "POOR 1"
	};

	let csg_cgc_grading_scale = {
		"g10perfect": "Perfect 10",
		"g10pristine": "Pristine 10",
		"g10": "Gem Mint 10",	
		"g9_5": "Mint+ 9.5",
		'g9': "Mint 9",
		'g8_5':  "NM-MT+ 8.5",
		'g8': "NM-MT 8",
		'g7_5': "NM+ 7.5",
		'g7': "NM 7",
		'g6_5': "EX-MT+ 6.5",
		'g6': "EX-MT 6",
		'g5_5': "EX+ 5.5",
		'g5': "EX 5",
		'g4_5': "VG-EX+ 4.5",
		'g4': "VG-EX 4",
		'g3_5': "VG+ 3.5",
		'g3': "VG 3",
		'g2_5': "GOOD+ 2.5",
		'g2': "GOOD 2",
		'g1_5': "FAIR 1.5",
		'g1': "POOR 1"
	};

	$(document).ready(function(){
		$("#search").on('input', function(){
			let query = $(this).val();
			if(query.length >= 5){
				// Call your backend search function here
				searchAtlas(query);
			} else {
				// If the input length is less than 5, hide the results
				$("#results").hide();
			}
		});

		// Hide results if clicking outside the input and results list
		$(document).click(function(event) {
			// Check if clicked element or its parents are not the input or the results list
			if (!$(event.target).closest("#search, #results").length) {
				$("#results").hide();
			}
		});
	});

	$(document).ready(function() {
		console.log("Document ready, gemrateId:", gemrateId);
		
		// Initialize currentGemrateId
		currentGemrateId = gemrateId;
		
		// Initialize page based on gemrateId
		if (!gemrateId || gemrateId === "" || gemrateId === "None") {
			console.log("Showing suggestions");
			$('#suggestions').show();
			$('#search').focus();
			
			// Hide results containers
			$('#summary-info, #gradesTable, #pieWrapper, #popWrapper, #gemWrapper').hide();
		} else {
			console.log("Attempting to fetch card details for:", gemrateId);
			$('#suggestions').hide();
			fetchCardDetails(gemrateId);
		}

		$('.suggestion-box').on('click', function() {
			const query = $(this).data('query');
			$('#search').val(query);
			searchAtlas(query);

			// Analytics event tracking
			analytics.track('Suggestion Box Clicked', {
				query: query
			});
		});
	});

	function searchAtlas(query) {
		jQuery.ajax({
			url: '/universal-search-query', // Flask default URL
			method: 'POST',
			contentType: "application/json",
			data: JSON.stringify({ query: query }),
			success: function(data) {
				$("#results").empty();
				data.forEach(item => {
					let formattedPopulation = item.total_population.toLocaleString('en-US');
					
					// Convert population_type to lowercase to match the graderColors keys
					let populationTypeLower = item.population_type.toLowerCase();

					// Check if population_type is 'Universal'
					if (populationTypeLower.toUpperCase() === 'UNIVERSAL') {
						badgeColor = '#009999'; // Specific color for 'Universal'
					} else {
						// Determine the color based on population_type
						badgeColor = graderColors[populationTypeLower] || '#007bff'; // Default color if not found
					}
					
					let listItem = `
						<li class="list-group-item card-item" data-gemrate-id="${item.gemrate_id}">
							<b>${item.description.replace('Base ', '')}</b>
							<span class="badge" style="background-color: ${badgeColor}; color: white;">${populationTypeLower.toUpperCase()}</span>
							<span class="badge badge-primary"> Total Graded: ${formattedPopulation}</span>
						</li>
					`;
					$("#results").append(listItem);
				});

				$(".card-item").on("click", function() {
					const gemrateId = $(this).data("gemrate-id");
					fetchCardDetails(gemrateId);
				});

				// Show the results list here
				$("#results").show();
			}
		});
	}

let charts = {};
const cardDetailsToken = "eyJ0cyI6MTc2Nzg4ODE5NCwiaWQiOiIyNjAzOjgwMDA6YjAwMDpiMTIzOjEwMzY6NjZlZTplNzkyOjE5YTEifQ.43774932a2abde90617fc4a3b145ec507c5816556473c666e693c6a0a85efdc1";

	const graderMapper = {
		psa: {
			'Total': 'card_total_grades',
			'GemsPlus': 'card_gems',
			'GemPercent': 'card_gem_rate',
			'A': 'auth',
			'1': 'g1',
			'1.5': 'g1_5',
			'2': 'g2',
			'2.5': 'g2_5',
			'3': 'g3',
			'3.5': 'g3_5',
			'4': 'g4',
			'4.5': 'g4_5',
			'5': 'g5',
			'5.5': 'g5_5',
			'6': 'g6',
			'6.5': 'g6_5',
			'7': 'g7',
			'7.5': 'g7_5',
			'8': 'g8',
			'8.5': 'g8_5',
			'Mint': 'g9',
			'Mint+': null, 
			'GM MT': 'g10',
			'Pri': null, 
			'Per': null
		},
		beckett: {
			'Total': 'card_total_grades',
			'GemsPlus': 'card_gems',
			'GemPercent': 'card_gem_rate',
			'A': null, 
			'1': 'g1',
			'1.5': 'g1_5',
			'2': 'g2',
			'2.5': 'g2_5',
			'3': 'g3',
			'3.5': 'g3_5',
			'4': 'g4',
			'4.5': 'g4_5',
			'5': 'g5',
			'5.5': 'g5_5',
			'6': 'g6',
			'6.5': 'g6_5',
			'7': 'g7',
			'7.5': 'g7_5',
			'8': 'g8',
			'8.5': 'g8_5',
			'Mint': 'g9',
			'Mint+': null,
			'GM MT': 'g9_5', 
			'Pri': 'g10p', 
			'Per': 'g10b'
		},
		sgc: {
			'Total': 'card_total_grades',
			'GemsPlus': 'card_gems',
			'GemPercent': 'card_gem_rate',
			'A': 'gA',
			'1': 'g1',
			'1.5': 'g1_5',
			'2': 'g2',
			'2.5': 'g2_5',
			'3': 'g3',
			'3.5': 'g3_5',
			'4': 'g4',
			'4.5': 'g4_5',
			'5': 'g5',
			'5.5': 'g5_5',
			'6': 'g6',
			'6.5': 'g6_5',
			'7': 'g7',
			'7.5': 'g7_5',
			'8': 'g8',
			'8.5': 'g8_5',
			'Mint': 'g9',
			'Mint+': 'g9_5',
			'GM MT': 'g10',
			'Pri': 'g10p',
			'Per': null
		},
		cgc: {
			'Total': 'card_total_grades',
			'GemsPlus': 'card_gems',
			'GemPercent': 'card_gem_rate',
			'A': null, 
			'1': 'g1',
			'1.5': 'g1_5',
			'2': 'g2',
			'2.5': 'g2_5',
			'3': 'g3',
			'3.5': 'g3_5',
			'4': 'g4',
			'4.5': 'g4_5',
			'5': 'g5',
			'5.5': 'g5_5',
			'6': 'g6',
			'6.5': 'g6_5',
			'7': 'g7',
			'7.5': 'g7_5',
			'8': 'g8',
			'8.5': 'g8_5',
			'Mint': 'g9',
			'Mint+': 'g9_5',
			'GM MT': 'g10', 
			'Pri': 'g10pristine', 
			'Per': 'g10perfect'
		}
	};

	const gradeOrder = ['Total', 'GemsPlus', 'GemPercent', 'Per', 'Pri', 'GM MT', 'Mint+', 'Mint', '8.5', '8', '7.5', '7', '6.5', '6', '5.5', '5', '4.5', '4', '3.5', '3', '2.5', '2', '1.5', '1', 'A', 'Advanced'];
	const grade_to_percent_map = {
		'Per': 'total_perfect', 'Pri': 'total_pristine', 'GM MT': 'total_gem_mint', 'Mint+': 'total_mint_plus', 'Mint': 'total_9', '8.5': 'total_8_5', '8': 'total_8', '7.5': 'total_7_5', '7': 'total_7', '6.5': 'total_6_5', '6': 'total_6', '5.5': 'total_5_5', '5': 'total_5', '4.5': 'total_4_5', '4': 'total_4', '3.5': 'total_3_5', '3': 'total_3', '2.5': 'total_2_5', '2': 'total_2', '1.5': 'total_1_5', '1': 'total_1'	, 'A': 'total_auth'
	};
	const grade_to_higher_map = {
		'Per': 'total_perfect_higher', 'Pri': 'total_pristine_higher', 'GM MT': 'total_gem_mint_higher', 'Mint+': 'total_mint_plus_higher', 'Mint': 'total_9_higher', '8.5': 'total_8_5_higher', '8': 'total_8_higher', '7.5': 'total_7_5_higher', '7': 'total_7_higher', '6.5': 'total_6_5_higher', '6': 'total_6_higher', '5.5': 'total_5_5_higher', '5': 'total_5_higher', '4.5': 'total_4_5_higher', '4': 'total_4_higher', '3.5': 'total_3_5_higher', '3': 'total_3_higher', '2.5': 'total_2_5_higher', '2': 'total_2_higher', '1.5': 'total_1_5_higher', '1': 'total_1_higher'	, 'A': 'total_auth_higher'
	};

	Chart.defaults.font.color = '#000';

	function fetchCardDetails(gemrateId) {
		console.log("fetchCardDetails called with:", gemrateId);
		
		if (!gemrateId || gemrateId === "" || gemrateId === "None") {
			console.error("Invalid gemrateId:", gemrateId);
			return;
		}

		// Reset any previous state
		$('#pieWrapper, #popWrapper, #gemWrapper, #gradeWrapper, #psaWrapper, #beckettWrapper, #sgcWrapper, #cgcWrapper').hide();
		$('#suggestions').hide();
		
		$.ajax({
			url: '/card-details',
			method: 'GET',
			data: { gemrate_id: gemrateId },
			headers: {
				'X-Card-Details-Token': cardDetailsToken
			},
			beforeSend: function() {
				console.log("Sending request for gemrateId:", gemrateId); // Debug log
			},
			success: function(data) {
				console.log("Card data received:", data); // Debug log
				if (data) {
					// Show containers before populating
					$('#summary-info, #gradesTable').show();
					
					// Store the current gemrateId
					currentGemrateId = gemrateId;
					
					// Update the URL if it's not already correct
					const currentUrl = new URL(window.location.href);
					if (currentUrl.searchParams.get('gemrate_id') !== gemrateId) {
						currentUrl.searchParams.set('gemrate_id', gemrateId);
						window.history.pushState({}, '', currentUrl);
					}
					
					analytics.track('Card Details Loaded', {
						gemrateId: gemrateId,
						description: data.description,
						population_type: data.population_type,
						total_population: data.total_population,
						graders_included: data.graders_included
					});

					cardDetailsData = data;

					// Remove any existing buttons
					$('.d-block.d-md-none.text-center').remove();  // Remove mobile button
					$('#search-table-wrapper .d-none.d-md-block.text-center').remove();  // Remove desktop button with more specific selector

					// Add mobile button
					const urlParam = data.population_type === "grader-specific" ? "gemRateId" : "universalGemRateId";
					const graderText = data.population_type === "grader-specific" && data.graders_included.length > 0 
						? data.graders_included[0].toUpperCase() 
						: "Graded";
					const cardLadderUrl = `https://app.cardladder.com/search?${urlParam}=${currentGemrateId}&via=gemrate`;

					const mobileButtonHtml = `
						<div class="d-block d-md-none text-center mt-2 mb-2">
							<a href="${cardLadderUrl}" 
							   target="_blank" 
							   class="btn btn-sm btn-outline-primary"
							   style="background-color: transparent; color: #34be8b; border-color: #34be8b; font-size: 80%;"
							   onmouseover="this.style.backgroundColor='#34be8b'; this.style.color='white';"
							   onmouseout="this.style.backgroundColor='transparent'; this.style.color='#34be8b';"
							   onclick="analytics.track('CardLadder Link Clicked', {
								   gemrateId: '${currentGemrateId}',
								   description: '${data.description}',
								   population_type: '${data.population_type}',
								   total_population: ${data.total_population},
								   grader: '${data.population_type === "grader-specific" ? data.graders_included[0] : "all"}',
								   device: 'mobile',
								   cardladder_url: '${cardLadderUrl}'
							   });">
								View all <u>${graderText} Sales</u> on CardLadder
								<span class="material-icons-outlined" 
									  style="font-size: 12px; vertical-align: middle; cursor: help;" 
									  title="While this link is a valuable resource - it is also an affiliate link. There is zero pressure to purchase. However, if you do click and subscribe to CardLadder, GemRate may earn a commission at no additional cost to you.">
									info
								</span>
							</a>
						</div>
					`;
					$('#gradesTable').before(mobileButtonHtml);

					// Add desktop button
					const desktopButton = document.createElement('div');
					desktopButton.className = 'd-none d-md-block text-center mt-2 mb-2';
					desktopButton.innerHTML = `
						<a href="${cardLadderUrl}" 
						   target="_blank" 
						   class="btn btn-sm btn-outline-primary"
						   style="background-color: #34be8b; color: white; border-color: #34be8b; font-size: 80%;"
						   onmouseover="this.style.backgroundColor='transparent'; this.style.color='#34be8b';"
						   onmouseout="this.style.backgroundColor='#34be8b'; this.style.color='white';"
						   onclick="analytics.track('CardLadder Link Clicked', {
							   gemrateId: '${currentGemrateId}',
							   description: '${data.description}',
							   population_type: '${data.population_type}',
							   total_population: ${data.total_population},
							   grader: '${data.population_type === "grader-specific" ? data.graders_included[0] : "all"}',
							   device: 'desktop',
							   cardladder_url: '${cardLadderUrl}'
						   });">
							View all <u>${graderText} Sales</u> of this card on CardLadder
							<span class="material-icons-outlined" 
								  style="font-size: 12px; vertical-align: middle; cursor: help;" ar
								  title="While this link is a valuable resource - it is also an affiliate link. There is zero pressure to purchase. However, if you do click and subscribe to CardLadder, GemRate may earn a commission at no additional cost to you.">
								info
							</span>
						</a>
					`;
					document.getElementById('search-table-wrapper').appendChild(desktopButton);

					// Initialize totals
					const totals = {};

					function displayStandardTable(data) {
						$('#gradesTable').show();
						const table = document.getElementById('gradesTable').getElementsByTagName('tbody')[0];
						table.innerHTML = '';

						gradeOrder.forEach(gradeKey => {
							if (!['GemPercent'].includes(gradeKey)) {
								totals[gradeKey] = 0;
							}
						});

						// Function to create a table row
						function createRow(graderData, originalGraderKey) {
							let graderKey = originalGraderKey.toLowerCase();
							let graderUrl = graderData.set_url; // Fetch the set_url from graderData
							let graderDescription = graderData.description.replace('Base ', '') || ''; // Fetch the details from graderData

							let row = '<tr>';
							// Add Grader Name with hyperlink and tooltip
							if (graderUrl) {
								row += `<td style="background: #fafafa;"><a href="${graderUrl}" title="${graderDescription}" target="_blank" onclick="analytics.track('Grader Link Clicked', {
									grader: '${graderKey.toUpperCase()}',
									description: '${graderDescription}',
									gemrateId: '${currentGemrateId}',
									grader_url: '${graderUrl}',
									source: 'universal_search',
									device: 'desktop'
								});">${graderKey.toUpperCase()}</a></td>`;
							} else {
								row += `<td style="background: #fafafa;">${graderKey.toUpperCase()}</td>`;
							}

							// Iterate through each grade in the specified order
							gradeOrder.forEach(gradeKey => {
								let gradeValue;
								if (gradeKey === 'Total' || gradeKey === 'GemsPlus' || gradeKey === 'GemPercent') {
									if (gradeKey === 'GemPercent') {
										gradeValue = (graderData[graderMapper[graderKey][gradeKey]] * 100).toFixed(1) || '-';
										row += `<td style="background: #fafafa;">${gradeValue}%</td>`;
									} else {
										gradeValue = graderData[graderMapper[graderKey][gradeKey]] || '-';
										row += `<td style="background: #fafafa;">${gradeValue.toLocaleString()}</td>`;
									}
								} else if (gradeKey === 'Advanced') {
									// Generate advanced URL link
									const advancedUrl = generateAdvancedUrl(graderData, graderKey);
									row += `<td style="background: #fafafa;"><a href="${advancedUrl}" target="_blank" style="color: #009999; text-decoration: none;" onclick="analytics.track('Pop Report Link Clicked', {
										grader: '${graderKey.toUpperCase()}',
										description: '${graderDescription}',
										gemrateId: '${currentGemrateId}',
										pop_report_url: '${advancedUrl}',
										source: 'universal_search',
										device: 'desktop'
									});">Link</a></td>`;
								} else {
									if (graderKey === 'psa') {
										// Separate handling for PSA half grades
										gradeValue = graderData.grades[graderMapper[graderKey][gradeKey]] || graderData.halves[graderMapper[graderKey][gradeKey]] || '-';
									} else {
										gradeValue = graderData.grades[graderMapper[graderKey][gradeKey]] || '-';
									}
									row += `<td>${gradeValue.toLocaleString()}</td>`;
								}
								// Update totals
								if (!['GemPercent', 'Advanced'].includes(gradeKey)) {
									totals[gradeKey] += isNaN(gradeValue) ? 0 : parseInt(gradeValue);
								}
							});

							row += '</tr>';
							return row;
						}

						// Iterate through each grader in payload
						data.population_data.forEach(graderData => {
							let graderKey = graderData.grader.toLowerCase();
							table.innerHTML += createRow(graderData, graderKey);
						});

						// Calculate Gem % for totals
						let totalGemPercent = totals['GemsPlus'] / totals['Total'] * 100;

						// Create and append the totals row
						let totalsRow = '<tr><td style="background: #fafafa;"><strong>Total</strong></td>';
						gradeOrder.forEach(gradeKey => {
							if (gradeKey === 'GemPercent') {
								totalsRow += `<td style="background: #fafafa;"><strong>${totalGemPercent.toFixed(1)}%</strong></td>`;
							} else if (gradeKey === 'Advanced') {
								totalsRow += `<td style="background: #fafafa;"><strong>-</strong></td>`;
							} else {
								updatedTotal = totals[gradeKey]===0 ? '-' : totals[gradeKey].toLocaleString();
								totalsRow += `<td style="background: #fafafa;"><strong>${updatedTotal}</strong></td>`;
							}
						});
						totalsRow += '</tr>';
						table.innerHTML += totalsRow;

						table.innerHTML += '<tr><td style="height: 5px; border:none;" colspan="27"></td></tr>';

						let percentagesRow = '<tr><td style="background: #fafafa; font-size: 85%;"><strong>Grade %</strong></td>';
						gradeOrder.forEach(gradeKey => {
							if (gradeKey == 'GemPercent' || gradeKey == 'Total' || gradeKey == 'GemsPlus' || gradeKey == 'Advanced') {
								percentagesRow += `<td style="background: #fafafa;">-</td>`; // Placeholder for non-percentage columns
							} else {
								let percentageValue = (totals[gradeKey] / totals['Total']) * 100 || 0;
								percentagesRow += `<td style="background: #fafafa;">${percentageValue.toFixed(1)}%</td>`;
							}
						});
						percentagesRow += '</tr>';
						table.innerHTML += percentagesRow;

						const percent_higher = data.percent_higher;
						let higherRow = '<tr><td style="background: #fafafa; font-size: 85%;"><strong>% Higher</strong></td>';
						gradeOrder.forEach(gradeKey => {
							if (gradeKey == 'GemPercent' || gradeKey == 'Total' || gradeKey == 'GemsPlus' || gradeKey == 'Advanced') { // Exclude non-grade columns from percentage calculation
								higherRow += `<td style="background: #fafafa;">-</td>`; // Placeholder for non-grade columns
							} else {
								let temp_value = grade_to_higher_map[gradeKey]
								higherRow += `<td style="background: #fafafa;">${percent_higher[temp_value].toFixed(1)}%</td>`;
							}
						});
						higherRow += '</tr>';
						table.innerHTML += higherRow;

					}

					$('#pieWrapper, #popWrapper, #gemWrapper, #gradeWrapper, #psaWrapper, #beckettWrapper, #sgcWrapper, #cgcWrapper').show();
					
					populateElementsWithData(data);
					$('#summary-info').show();

					function rearrangeTableForMobile(data) {
						const mobileTable = document.createElement('table');
						mobileTable.id = 'gradesTable';
						mobileTable.className = 'responsive-table mb-3';

						// Create header row with grader names
						let headerRow = '<tr><th>Grade</th>';
						data.population_data.forEach(graderData => {
							let graderKey = graderData.grader.toLowerCase();
							let graderUrl = graderData.set_url; // Fetch the set_url from graderData
							let graderDescription = graderData.description.replace('Base ', '') || ''; // Fetch the details from graderData
							if (graderUrl) {
								headerRow += `<th style="text-align: center;"><a href="${graderUrl}" title="${graderDescription}" target="_blank" onclick="analytics.track('Grader Link Clicked', {
									grader: '${graderKey.toUpperCase()}',
									description: '${graderDescription}',
									gemrateId: '${currentGemrateId}',
									grader_url: '${graderUrl}',
									source: 'universal_search',
									device: 'mobile'
								});">${graderKey.toUpperCase()}</a></th>`;
							} else {
								headerRow += `<th style="text-align: center;">${graderKey.toUpperCase()}</th>`;
							}
						});
						headerRow += '<th style="text-align: center;">Total</th>';
						headerRow += '<th style="text-align: center;">Grade %</th>';
						headerRow += '<th style="text-align: center;">% Higher</th></tr>';
						
						mobileTable.innerHTML += headerRow;

						//const gradeOrderMobile = ['Total', 'GemsPlus', 'GemPercent','Per', 'Pri', 'GM MT', 'Mint+', 'Mint', '8.5', '8', '7.5', '7', '6.5', '6', '5.5', '5', '4.5', '4', '3.5', '3', '2.5', '2', '1.5', '1', 'A'];
						const mobileHeader = {'Total': 'Total', 'GemsPlus': 'Gems+', 'GemPercent': 'Gem Rate', 'Per': 'Perfect', 'Pri': 'Pristine', 'GM MT': 'Gem Mint', 'Mint+': 'Mint+', 'Mint': 'Mint', '8.5': '8.5', '8': '8', '7.5': '7.5', '7': '7', '6.5': '6.5', '6': '6', '5.5': '5.5', '5': '5', '4.5': '4.5', '4': '4', '3.5': '3.5', '3': '3', '2.5': '2.5', '2': '2', '1.5': '1.5', '1': '1', 'A': 'A', 'Advanced': '<span class="material-icons-outlined" style="font-size: 16px; vertical-align: middle;" title="Pop Report">article</span>'};

						let mobileGrades = 0;
						let mobileGems = 0;
						// Add data rows
						// Iterate through each grade in the specified order
						gradeOrder.forEach(gradeKey => {
							let row = `<tr><td style="background: #fafafa;"><strong>${mobileHeader[gradeKey]}</strong></td>`;
							let totalMobile = 0;
						
							// Handle Advanced row separately
							if (gradeKey === 'Advanced') {
								// For Advanced row, show links for each grader
								data.population_data.forEach(graderData => {
									const advancedUrl = generateAdvancedUrl(graderData, graderData.grader);
									const graderDescription = graderData.description.replace('Base ', '') || '';
									row += `<td style="text-align: center;"><a href="${advancedUrl}" target="_blank" style="color: #009999; text-decoration: none;" onclick="analytics.track('Pop Report Link Clicked', {
										grader: '${graderData.grader.toUpperCase()}',
										description: '${graderDescription}',
										gemrateId: '${currentGemrateId}',
										pop_report_url: '${advancedUrl}',
										source: 'universal_search',
										device: 'mobile'
									});">Link</a></td>`;
								});
							} else {
								// Iterate through each grader in payload for regular grade rows
								data.population_data.forEach(graderData => {
									let graderKey = graderData.grader.toLowerCase();
									let gradeValue;
									if (gradeKey === 'Total') {
										gradeValue = graderData[graderMapper[graderKey][gradeKey]] || '-';
										row += `<td style="text-align: center;">${gradeValue.toLocaleString()}</td>`;
										totalMobile += isNaN(gradeValue) ? 0 : parseInt(gradeValue);
										mobileGrades = totalMobile;
									} else if (gradeKey === 'GemsPlus') {
										gradeValue = graderData[graderMapper[graderKey][gradeKey]] || '-';
										row += `<td style="text-align: center;">${gradeValue.toLocaleString()}</td>`;
										totalMobile += isNaN(gradeValue) ? 0 : parseInt(gradeValue);
										mobileGems = totalMobile;
									} else if (gradeKey === 'GemPercent') {
										let gems = graderData[graderMapper[graderKey]['GemsPlus']] || 0;
										let total = graderData[graderMapper[graderKey]['Total']] || 0;
										gradeValue = total > 0 ? ((gems / total) * 100).toFixed(1) + '%' : '-';
										row += `<td style="text-align: center;">${gradeValue}</td>`;
									} else {
										if (graderKey === 'psa') {
											// Separate handling for PSA half grades
											gradeValue = graderData.grades[graderMapper[graderKey][gradeKey]] || graderData.halves[graderMapper[graderKey][gradeKey]] || '-';
										} else {
											gradeValue = graderData.grades[graderMapper[graderKey][gradeKey]] || '-';
										}
										totalMobile += isNaN(gradeValue) ? 0 : parseInt(gradeValue);
										row += `<td style="text-align: center;">${gradeValue.toLocaleString()}</td>`;
									}
								});
							}
							
							// Add totals and percentage columns
							if (gradeKey === 'GemPercent') {
								//console.log('mobileGrades', mobileGrades);
								let totalGemPercent = mobileGrades > 0 ? (mobileGems / mobileGrades * 100).toFixed(1) : '-';
								row += `<td style="background: #fafafa; text-align: center;"><strong>${totalGemPercent}%</strong></td>`;
							} else if (gradeKey === 'Advanced') {
								row += `<td style="background: #fafafa; text-align: center;"><strong>-</strong></td>`;
							} else {
								let updatedTotal = totalMobile === 0 ? '-' : totalMobile.toLocaleString();
								row += `<td style="background: #fafafa; text-align: center;"><strong>${updatedTotal}</strong></td>`;
							}

							const grade_percent = data.percent_of_total;
							const percent_higher = data.percent_higher;
							
							if (gradeKey == 'GemPercent' || gradeKey == 'Total' || gradeKey == 'GemsPlus' || gradeKey == 'Advanced') { // Exclude non-grade columns from percentage calculation
								row += `<td style="text-align: center;">-</td>`; // Placeholder for non-grade columns
							} else {
								let temp_value = grade_to_percent_map[gradeKey]
								row += `<td style="text-align: center;">${grade_percent[temp_value].toFixed(1)}%</td>`;
							}

							if (gradeKey == 'GemPercent' || gradeKey == 'Total' || gradeKey == 'GemsPlus' || gradeKey == 'Advanced') { // Exclude non-grade columns from percentage calculation
								row += `<td style="text-align: center;">-</td>`; // Placeholder for non-grade columns
							} else {
								let temp_value = grade_to_higher_map[gradeKey]
								row += `<td style="text-align: center;">${percent_higher[temp_value].toFixed(1)}%</td>`;
							}

							// No Advanced column on mobile - it's just a row

							row += '</tr>';
							mobileTable.innerHTML += row;
						});

						const existingTable = document.getElementById('gradesTable');
						if (existingTable) {
							existingTable.parentNode.replaceChild(mobileTable, existingTable);
						} else {
							console.error('The gradesTable element was not found.');
						}
					}

					const summaryInfo = document.getElementById("summary-info");

					summaryInfo.innerHTML = `
					<h2 class="card-title search-details" style="color: #000;">Universal Population Details</h2>
					
					<div class="info-container">
						<h5 class="my-3 py-2 px-md-4 px-2 summary-stats" style="border-radius: 0.25rem;">${data.description.replace('Base ', '')}</h5>
						<div class="info-row">
							<div class="summary-stats population-details" style="border-radius: 0.25rem;">Total Population: ${Number(data.total_population).toLocaleString()}</div>
							<div class="summary-stats total-population" style="border-radius: 0.25rem;">Gem Rate - All Graders: ${parseFloat(data.total_gems_or_greater / data.total_population * 100).toFixed(1)}%</div>
						</div>
					</div>
					`;

					if (window.innerWidth <= 1300) {
						rearrangeTableForMobile(data);
					} else {
						displayStandardTable(data);
					}

					var element = document.querySelector('.card-title.search-details');
					if (element) {
						element.scrollIntoView({ behavior: 'smooth', block: 'start' });
					}
				}
			},
			error: function(xhr) {
				if (xhr.status === 403) {
					// Token expired - prompt user to refresh the page to get a new token
					if (confirm('Your session has expired. Would you like to refresh the page to continue?')) {
						window.location.reload();
					}
				} else {
					console.error("Error fetching card details:", xhr);
				}
			}
		});
	}

	function destroyCharts() {
		for (let chart in charts) {
			if (charts[chart] != null) {
				charts[chart].destroy(); // Destroy the chart
				charts[chart] = null; // Set to null to clean up
			}
		}
	}

	function filterGrades(grades) {
		let totalCount = 0;
		let _5Count = 0;
		
		Object.entries(grades).forEach(([key, value]) => {
			if (key.includes('_5')) {
				_5Count += value;
			}
			totalCount += value;
		});
		
		return { grades, totalCount, _5Count };
	}

	function populateElementsWithData(data) {
		// Show all relevant elements
		$('#pieWrapper, #popWrapper, #gemWrapper, #gradeWrapper').show();
		
		// Render the charts with the data
		renderCharts(data);
	}

	function renderCharts(data) {
		if (data && data.graders_included && data.population_data) {
			destroyCharts();
			
			// First, hide all chart wrappers and remove any existing charts
			$('#pieWrapper, #popWrapper, #gemWrapper, #gradeWrapper, #psaWrapper, #beckettWrapper, #sgcWrapper, #cgcWrapper').hide();
			
			// Show the universal charts (pie, pop, gem)
			$('#pieWrapper, #popWrapper, #gemWrapper').show();
			
			// Only show wrappers for graders that are included in the data
			data.graders_included.forEach(grader => {
				const graderLower = grader.toLowerCase();
				// Map 'beckett' to the correct wrapper ID
				const wrapperId = graderLower === 'beckett' ? 'beckettWrapper' : `${graderLower}Wrapper`;
				$(`#${wrapperId}`).show();
				
				// Add CSS to remove any margin/padding that might create gaps
				$(`#${wrapperId}`).css({
					'margin-bottom': '20px',
					'margin-top': '0'
				});
			});

			let graders = data.graders_included.map(grader => {
				return grader.toUpperCase();
			});
			let gradeLabels = graders;

			data.graders_included.forEach(grader => {
				const summary = data.population_data.find(item => {
					return item.grader && item.grader.toUpperCase() === grader.toUpperCase();
				});
				
				if (summary) {
					const { grades, totalCount, _5Count } = filterGrades(summary.grades);
					const _5Percentage = (_5Count / totalCount) * 100;
					let finalGrades = grades;
					
					if (grader === "psa" && _5Percentage < 2) {
						finalGrades = Object.keys(grades)
							.filter(key => !key.includes('_5'))
							.reduce((obj, key) => {
								obj[key] = grades[key];
								return obj;
							}, {});
					}

					const sortedLabels = gradingLists[grader].filter(grade => grade in finalGrades);
					const sortedData = sortedLabels.map(label => finalGrades[label] || 0);
					const graderColor = graderColors[grader] || 'rgba(75, 192, 192, 0.2)';  // Default color if the grader isn't in the mapping
					
					const ctx = document.getElementById(`${grader}Chart`).getContext('2d');
					charts[grader] = new Chart(ctx, {
						type: 'bar',
						plugins: [ChartDataLabels],
						data: {
							labels: sortedLabels,
							datasets: [{
								label: grader,
								data: sortedData,
								backgroundColor: graderColor,
								borderColor: graderColor,
								borderWidth: 1
							}]
						},
						options: {
							scales: {
								y: {
									beginAtZero: true,
									grid: {
										display: false
									}
								}
							},
							plugins: {
								title: {
									display: true,
									text: `Grade Distribution - ${grader.toLowerCase() === "beckett" ? "Beckett" : grader.toUpperCase()}`,
									color: '#000',
									font: {
										size: 16
									},
									padding: 20
								},
								legend: {
									display: false
								},
								datalabels: {
									color: '#000',
									anchor: 'end',  
									align: 'top',
									formatter: function(value, context) {
										return value > 0 ? value.toLocaleString() : '';
									}
								}
							}
						}
					});
				} else {
				// Hide the canvas wrapper if no data exists for the grader
				document.getElementById(`${grader}Wrapper`).style.display = 'none';
				}
			});

			const ctx = document.getElementById('popChart').getContext('2d');

			const cardPopulations = data.population_data.map(item => item.card_total_grades);
			const maxPopValue = Math.max(...cardPopulations);
			const popYAxisMax = roundUpToNearestTenPower(maxPopValue + 0.25 * maxPopValue);

			const pieLabels = graders;
			const pieData = data.population_data.map(item => item.card_total_grades);
			const pieBackgroundColor = pieLabels.map(label => graderColors[label.toLowerCase()]);
			const barLabels = graders;
			const barBackgroundColor = barLabels.map(label => graderColors[label.toLowerCase()]);

			const totalCards = pieData.reduce((acc, num) => acc + num, 0);

			const pieCtx = document.getElementById('pieChart').getContext('2d');

			charts['totalGradesChart'] = new Chart(pieCtx, {
				type: 'doughnut',
				data: {
					labels: pieLabels,
					datasets: [{
						data: pieData,
						backgroundColor: pieBackgroundColor,
					}]
				},
				options: {
					plugins: {
						title: {
							display: true,
							text: 'Universal Population: Total Grades by Grader',
							color: '#000',
							font: {
								size: 16
							}
						},
						legend: {
							position: 'bottom'
						},

						tooltip: {
							callbacks: {
								label: function(context) {
									const label = context.label;
									const value = context.parsed;
									const percentage = ((value / totalCards) * 100).toFixed(1);
									return `${label}: ${value.toLocaleString()} (${percentage}%)`;
								}
							}
						}
					},
				}
			});

			const popData = {
				labels: gradeLabels,
				datasets: [{
					label: 'Card Population',
					data: cardPopulations,
					backgroundColor: barBackgroundColor
				}]
			};

			const popConfig = {
				type: 'bar',
				data: popData,
				plugins: [ChartDataLabels],
				options: {
					scales: {
						y: {
							beginAtZero: true,
							max: popYAxisMax
						}
					},
					plugins: {
						title: {
							display: true,
							text: 'Universal Population: Total Grades by Grader',
							font: {
								size: 16,
							},
							color: '#000',
							padding: {
								top: 10,
								bottom: 30
							}
						},
						legend: {
							display: false
						},
						tooltip: {
							callbacks: {
								label: function(context) {
									return context.dataset.label + ": " + context.parsed.y;
								}
							}
						},
						datalabels: {
							color: '#000',
							anchor: 'end',
							align: 'top',
							formatter: function(value, context) {
								return value > 0 ? value.toLocaleString() : '';
							}
						}
					}
				}
			};

			charts['popChart'] = new Chart(ctx, popConfig);


			const ctx_ = document.getElementById('gemChart').getContext('2d');

			const gemRates = data.population_data.map(item => parseFloat(item.card_gem_rate * 100).toFixed(1));
			const maxGemRates = Math.max(...gemRates);
			const gemYAxisMax = Math.max(1, Math.min(roundUpToNearestTenPower(maxGemRates + 0.25 * maxGemRates), 100));

			const gemData = {
				labels: gradeLabels,
				datasets: [{
					label: 'Gem Rate',
					data: gemRates,
					backgroundColor: barBackgroundColor
				}]
			};

			const gemConfig = {
				type: 'bar',
				data: gemData,
				plugins: [ChartDataLabels],
				options: {
					scales: {
						y: {
							beginAtZero: true,
							max: gemYAxisMax
						}
					},
					plugins: {
						title: {
							display: true,
							text: 'Universal Population: Gem Rate (%) by Grader',
							font: {
								size: 16,
							},
							color: '#000',
							padding: {
								top: 10,
								bottom: 30
							}
						},
						legend: {
							display: false
						},
						tooltip: {
							callbacks: {
								label: function(context) {
									return context.dataset.label + ": " + context.parsed.y;
								}
							}
						},
						datalabels: {
							color: '#000',
							anchor: 'end',
							align: 'top',
							formatter: function(value, context) {
								return value > 0 ? value + '%' : '';
							}
						}
					}
				}
			};

			charts['gemChart'] = new Chart(ctx_, gemConfig);

			const summaryInfo = document.getElementById("summary-info");

			summaryInfo.innerHTML = `
			<h2 class="card-title search-details" style="color: #000;">Universal Population Details</h2>
			
			<div class="info-container">
				<h5 class="my-3 py-2 px-md-4 px-2 summary-stats" style="border-radius: 0.5rem;">${data.description.replace('Base ', '')}</h5>
				<div class="info-row">
					<div class="summary-stats population-details" style="border-radius: 0.5rem;">Total Population: ${Number(data.total_population).toLocaleString()}</div>
					<div class="summary-stats total-population" style="border-radius: 0.5rem;">Gem Rate - All Graders: ${parseFloat(data.total_gems_or_greater / data.total_population * 100).toFixed(1)}%</div>
				</div>
			</div>
			`;
		}
	}

	function replaceBECKETTWithBGS(node) {
		if (node.nodeType === 3) { // Text node
		node.nodeValue = node.nodeValue.replace(/BECKETT/g, 'BGS');
		} else if (node.nodeType === 1) { // Element node
		Array.from(node.childNodes).forEach(replaceBECKETTWithBGS);
		}
	}

	// Mutation observer callback to handle changes in the DOM
	function handleMutations(mutations) {
		mutations.forEach(mutation => {
		mutation.addedNodes.forEach(replaceBECKETTWithBGS);
		});
	}

	// Create a new mutation observer
	const observer = new MutationObserver(handleMutations);

	// Start observing the body for added nodes
	observer.observe(document.body, { childList: true, subtree: true });

	document.getElementById("copyLinkButton").addEventListener("click", function() {
		var fullUrl = window.location.origin + `/universal-search?gemrate_id=${currentGemrateId}&utm_source=share&utm_medium=site`;

		// Copy `fullUrl` to clipboard
		navigator.clipboard.writeText(fullUrl).then(function() {
			// Show the message that the link was copied
			document.getElementById('copyMessage').style.display = 'inline';
			setTimeout(function() {
				document.getElementById('copyMessage').style.display = 'none';
			}, 1000);
		}, function(err) {
			console.error('Could not copy text: ', err);
		});
		analytics.track('Basic Share Clicked', {
			share_url: fullUrl
		});
	});

	function updateTableBasedOnWidth(data) {

	}

	// Initial fetch and table setup
	fetchCardDetails();

	// Add an event listener for the resize event
	// window.addEventListener('resize', () => {
	// 	if (window.innerWidth <= 768) {
	// 		rearrangeTableForMobile(cardDetailsData);
	// 	} else {
	// 		displayStandardTable(cardDetailsData);
	// 	}
	// });

