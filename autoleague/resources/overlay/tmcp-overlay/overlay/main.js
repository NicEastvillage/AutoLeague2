let POLL_INTERVAL = 100;
let JSON_PATH = 'data.json';
let ICONS = {
    "BALL": "⚽",
    "BOOST": "⛽",
    "DEMO": "💣",
    "READY": "✔️",
    "DEFEND": "🛡️",
}


let app = new Vue({
    el: '#app',
    data: {
        info: {}
    },
    methods: {
        async loadData() {
            try {
                const res = await $.get("data.json");
                this.info = JSON.parse(res);
            } catch (err) {
                console.error(err);
            }
        },
        format(value, precision=10) {
            return Math.round(value * precision) / precision;
        },
        icon(action_type) {
            return ICONS[action_type];
        },
        playerName(index) {
            return this.info.names[index];
        },
    },
    created: function() {
        this.loadData();
        setInterval(this.loadData, POLL_INTERVAL);
    }
});