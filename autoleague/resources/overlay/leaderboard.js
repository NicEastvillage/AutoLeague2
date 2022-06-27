const ranksTable = $("#ranks-table");

function updateLeaderboard(summary, current_match) {

    // Variables used to format the leaderboard
    let odd = true;

    // Find the names of bots playing in the current match
    let blue_players = current_match == null ? [] : current_match.blue.map(details => details.name)
    let orange_players = current_match == null ? [] : current_match.orange.map(details => details.name)

    // Generate leaderboard table
    ranksTable.html(summary.bots_by_rank
        .map(function (bot) {
            let background_class = odd ? "odd" : "even";
            odd = !odd;

            background_class = blue_players.includes(bot.bot_id) ? "playing-for-blue" : (
                orange_players.includes(bot.bot_id) ? "playing-for-orange" : background_class);

            // Win indicators
            let win_indicators = bot.wins
                .map(win => win ? "images/win.png" : "images/loss.png") // TODO: Close matches, image already made
                .map(img => `<img class="rank-win-indicator" src=${img} />`)
                .join("")

            return `
<div class="leaderboard-item ${background_class}">
    <div class="leaderboard-number"><p class="center">${bot.cur_rank}</p></div>
    <div class="rank-bot-name">${bot.bot_id}</div>
    <div class="leaderboard-games">${win_indicators}</div>
    <div class="leaderboard-points"></div>
</div>`
        })
        .join(""));
}
