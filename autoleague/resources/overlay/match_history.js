const matchesTable = $("#matches-table");

function updateMatchHistory(data) {

    // Variables used to format table
    let odd = true;

    matchesTable.html(data.matches
        .map(function (match) {
            let odd_class = odd ? "odd" : "even";
            odd = !odd;

            let blue_crown_class = match.blue_goals < match.orange_goals ? "hide" : ""
            let orange_crown_class = match.blue_goals > match.orange_goals ? "hide" : ""

            return `
<div class="match-item ${odd_class}">
    <div class="match-number"><p class="right">${match.index + 1})</p></div>
    <div class="match-names blue"><p class="center">${match.blue_names.join(", ")}</p></div>
    <div class="crown blue"><img class="${blue_crown_class}" src="images/match win blue.png" /></div>
    <div class="match-mid"><p class="center">${match.blue_goals} VS ${match.orange_goals}</p></div>
    <div class="crown orange"><img class="${orange_crown_class}" src="images/match win orange.png"/></div>
    <div class="match-names orange"><p class="center">${match.orange_names.join(", ")}</p></div>
</div>`
                }));
}