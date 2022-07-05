const ranksTable = $("#leaderboard-table");

function updateLeaderboard(summary, current_match) {

    // Variables used to format the leaderboard
    let odd = true;

    // Generate leaderboard table
    ranksTable.html(summary.bots_by_rank
        .map(function (bot) {
            let background_class = odd ? "odd" : "even";
            odd = !odd;

            // Win indicators
            let win_indicators = bot.games
                .map(game => "images/" + game + ".png")
                .map(img => `<img class="leaderboard-game-indicator" src=${img} />`)
                .join("")

            return `
<div class="leaderboard-item ${background_class}">
    <div class="leaderboard-number"><p class="center">${bot.cur_rank}</p></div>
    <div class="rank-bot-name">${bot.bot_id}</div>
    <div class="leaderboard-games">${win_indicators}</div>
    <div class="leaderboard-points">${bot.mmr}</div>
</div>`
        })
        .join(""));
}
