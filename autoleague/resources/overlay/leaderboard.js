const ranksTable = $("#ranks-table");

function updateLeaderboard(summary, current_match) {

    // Variables used to format the leaderboard
    let max_tickets = Math.log(Math.max(...summary.bots_by_rank.map(bot => bot.tickets)));
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

            // Decide rank movement indicator
            let rank_img_src = "images/rank " + (
                bot.old_rank == null ? "new" : (
                    bot.old_rank < bot.cur_rank ? "down" : (
                        bot.old_rank > bot.cur_rank ? "up" : "same"
                    )
                )
            ) + ".png";

            let mmrIncr = bot.old_mmr == null ? "(+)" : (
                (bot.mmr - bot.old_mmr >= 0 ? "(+" : "(") + (bot.mmr - bot.old_mmr) + ")"
            );

            let mmrColor = bot.old_mmr == null ? "#FFF05A" : (
                (bot.mmr - bot.old_mmr >= 0 ?
                    lerpColor("#7a7a80", "#00f000", Math.min(1.0, (bot.mmr - bot.old_mmr) / 20.0)) :
                    lerpColor("#7a7a80", "#f00000", Math.min(1.0, (bot.mmr - bot.old_mmr) / -20.0)))
            )

            let division = [
                "division-transistor",
                "division-circuit",
                "division-processor",
                "division-overclocked",
                "division-quantum",
            ][Math.min(Math.max(0, Math.floor(bot.mmr / 20.0)), 4)]

            // Win indicators
            let win_indicators = bot.wins.length > 6 ?
                `${bot.wins.filter(win => win).length}/${bot.wins.length}`
                : 
                bot.wins
                .map(win => win ? "images/win.png" : "images/loss.png")
                .map(img => `<img class="rank-win-indicator" src=${img} />`)
                .join("")

            // Ticket bar width
            let tickets_width = Math.max(40.0 * Math.log(bot.tickets) / max_tickets, 1);

            return `
<div class="rank-item ${background_class}">
    <div class="rank-division ${division}"></div>
    <div class="rank-number"><p class="center">${bot.cur_rank}</p></div>
    <div class="rank-movement"><img src="${rank_img_src}"/></div>
    <div class="rank-bot-name">${bot.bot_id}</div>
    <div class="rank-mmr"><p class="center">${bot.mmr}</p></div>
    <div class="rank-mmr-incr"><p class="center" style="color: ${mmrColor}">${mmrIncr}</p></div>
    <div class="rank-wins">${win_indicators}</div>
    <div class="rank-tickets" style="width: ${tickets_width}px"></div>
</div>`
        })
        .join(""));
}

function lerpColor(a, b, amount) {

    let ah = parseInt(a.replace(/#/g, ''), 16),
        ar = ah >> 16, ag = ah >> 8 & 0xff, ab = ah & 0xff,
        bh = parseInt(b.replace(/#/g, ''), 16),
        br = bh >> 16, bg = bh >> 8 & 0xff, bb = bh & 0xff,
        rr = ar + amount * (br - ar),
        rg = ag + amount * (bg - ag),
        rb = ab + amount * (bb - ab);

    return '#' + ((1 << 24) + (rr << 16) + (rg << 8) + rb | 0).toString(16).slice(1);
}
