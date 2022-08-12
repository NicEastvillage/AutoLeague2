const matchesTable = $("#matches-table");

function updateMatchHistory(data) {
    matchesTable.html(data.matches
        .map(function (match) {

            let winClass = "";
            if (match.complete) {
                winClass = (match.blue_goals > match.orange_goals ? "blue" : "orange");
                winClass = winClass + (Math.abs(match.blue_goals - match.orange_goals) == 1 ? "-close" : "-win")
            }

            let blueSurrogateClasses = match.blue_names.map(bot => match.surrogate_names.includes(bot) ? "surrogate" : "")
            let orangeSurrogateClasses = match.orange_names.map(bot => match.surrogate_names.includes(bot) ? "surrogate" : "")
            console.log(orangeSurrogateClasses)

            return `
<div class="match-item ${winClass}">
    <p class="match-bot-name bot1 match-blue-name ${blueSurrogateClasses[0]}">${match.blue_names[0]},</p>
    <p class="match-bot-name bot2 match-blue-name ${blueSurrogateClasses[1]}">${match.blue_names[1]},</p>
    <p class="match-bot-name bot3 match-blue-name ${blueSurrogateClasses[2]}">${match.blue_names[2]}</p>
    <p class="match-bot-name bot4 match-orange-name ${orangeSurrogateClasses[0]}">${match.orange_names[0]},</p>
    <p class="match-bot-name bot5 match-orange-name ${orangeSurrogateClasses[1]}">${match.orange_names[1]},</p>
    <p class="match-bot-name bot6 match-orange-name ${orangeSurrogateClasses[2]}">${match.orange_names[2]}</p>
    <p class="match-score blue-score">${match.blue_goals}</p>
    <p class="match-score orange-score">${match.orange_goals}</p>
</div>`
                }));
}
