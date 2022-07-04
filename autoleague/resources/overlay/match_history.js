const matchesTable = $("#matches-table");

function updateMatchHistory(data) {
    matchesTable.html(data.matches
        .map(function (match) {

            let winClass = "";
            if (match.winner >= 0) {
                winClass = (match.winner == 0 ? "blue" : "orange");
                winClass = winClass + (Math.abs(match.blue_score - match.orange_score) == 1 ? "-close" : "-win")
            }

            let blueSurrogateClasses = match.blue.map(bot => bot in match.surrogate ? "surrogate" : "")
            let orangeSurrogateClasses = match.orange.map(bot => bot in match.surrogate ? "surrogate" : "")

            return `
<div class="match-item ${winClass}">
    <p class="match-bot-name bot1 ${blueSurrogateClasses[0]}">${match.blue[0]}</p>
    <p class="match-bot-name bot2 ${blueSurrogateClasses[1]}">${match.blue[1]}</p>
    <p class="match-bot-name bot3 ${blueSurrogateClasses[2]}">${match.blue[2]}</p>
    <p class="match-bot-name bot4 match-orange-name ${orangeSurrogateClasses[0]}">${match.orange[0]}</p>
    <p class="match-bot-name bot5 match-orange-name ${orangeSurrogateClasses[1]}">${match.orange[1]}</p>
    <p class="match-bot-name bot6 match-orange-name ${orangeSurrogateClasses[2]}">${match.orange[2]}</p>
    <p class="match-score blue-score">${match.blue_score}</p>
    <p class="match-score orange-score">${match.orange_score}</p>
</div>`
                }));
}
