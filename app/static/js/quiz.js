/**
 * クレジットカードおすすめ診断 - Quiz Logic
 * Prestige Black Theme
 */

const questions = [
    {
        id: "credit_level",
        text: "あなたのカード経験を教えてください",
        options: [
            { label: "初めての一枚（初心者）", value: "初心者" },
            { label: "数枚持っている（中級者）", value: "中級者" },
            { label: "ステータスカードを持ちたい（上級者）", value: "上級者" },
        ]
    },
    {
        id: "shopping",
        text: "ショッピングの頻度は？",
        options: [
            { label: "ほとんどしない", value: 1 },
            { label: "たまにする", value: 2 },
            { label: "よくする", value: 4 },
            { label: "毎日！Amazonヘビーユーザー", value: 5 },
        ]
    },
    {
        id: "travel",
        text: "旅行にはどのくらい行きますか？",
        options: [
            { label: "あまり行かない", value: 1 },
            { label: "年に1〜2回", value: 2 },
            { label: "年に3〜5回", value: 4 },
            { label: "頻繁に海外にも行く", value: 5 },
        ]
    },
    {
        id: "dining",
        text: "外食の頻度は？",
        options: [
            { label: "ほとんど外食しない", value: 1 },
            { label: "週1〜2回", value: 2 },
            { label: "週3〜4回", value: 3 },
            { label: "ほぼ毎日外食", value: 5 },
        ]
    },
    {
        id: "cashback",
        text: "キャッシュバック・ポイント還元はどのくらい重視しますか？",
        options: [
            { label: "重視しない", value: 1 },
            { label: "少し重視", value: 2 },
            { label: "かなり重視", value: 4 },
            { label: "最重要！とにかく還元率", value: 5 },
        ]
    },
    {
        id: "mobile",
        text: "スマホ決済（Apple Pay / Google Pay）を使いますか？",
        options: [
            { label: "使わない", value: 1 },
            { label: "たまに", value: 2 },
            { label: "よく使う", value: 4 },
            { label: "日常的に常に使う", value: 5 },
        ]
    },
    {
        id: "annual_fee_priority",
        text: "年会費についてどう考えていますか？",
        options: [
            { label: "絶対に無料がいい", value: true },
            { label: "条件付き無料ならOK", value: false },
            { label: "ステータスのためなら払う", value: false },
        ]
    },
];

let currentQuestion = 0;
let answers = {};
let selectedOption = null;

function startQuiz() {
    currentQuestion = 0;
    answers = {};
    selectedOption = null;
    document.getElementById("featuredSection").style.display = "none";
    document.querySelector(".hero").style.display = "none";
    document.getElementById("quizSection").style.display = "block";
    renderQuestion();
}

function renderQuestion() {
    const q = questions[currentQuestion];
    document.getElementById("quizQuestion").innerHTML = `<p>${q.text}</p>`;
    document.getElementById("progressText").textContent = `QUESTION ${currentQuestion + 1} / ${questions.length}`;
    document.getElementById("progressFill").style.width = `${((currentQuestion + 1) / questions.length) * 100}%`;

    const optionsHtml = q.options.map((opt, i) => {
        let cls = "quiz-option";
        if (selectedOption === i) cls += " selected";
        return `<div class="${cls}" onclick="selectOption(${i})">${opt.label}</div>`;
    }).join("");
    document.getElementById("quizOptions").innerHTML = optionsHtml;

    document.getElementById("btnBack").style.display = currentQuestion > 0 ? "block" : "none";
    const btnNext = document.getElementById("btnNext");
    btnNext.style.display = "block";
    btnNext.textContent = currentQuestion === questions.length - 1 ? "診断結果を見る" : "次へ";
}

function selectOption(index) {
    selectedOption = index;
    renderQuestion();
}

function prevQuestion() {
    if (currentQuestion > 0) {
        currentQuestion--;
        const q = questions[currentQuestion];
        const prevAns = answers[q.id];
        if (prevAns !== undefined) {
            selectedOption = q.options.findIndex(o => o.value === prevAns);
        } else {
            selectedOption = null;
        }
        renderQuestion();
    }
}

function nextQuestion() {
    if (selectedOption === null) {
        alert("選択してください");
        return;
    }

    const q = questions[currentQuestion];
    answers[q.id] = q.options[selectedOption].value;

    if (currentQuestion < questions.length - 1) {
        currentQuestion++;
        selectedOption = null;
        const nextQ = questions[currentQuestion];
        if (answers[nextQ.id] !== undefined) {
            selectedOption = nextQ.options.findIndex(o => o.value === answers[nextQ.id]);
        }
        renderQuestion();
    } else {
        submitQuiz();
    }
}

async function submitQuiz() {
    document.getElementById("quizSection").style.display = "none";

    const loadingHtml = `
        <div style="text-align:center; padding:80px 20px;">
            <div style="font-size:0.75rem; color:#c5a572; letter-spacing:0.3em; text-transform:uppercase; margin-bottom:24px;">ANALYZING</div>
            <div style="font-size:1.3rem; color:#fff; font-weight:600; margin-bottom:16px;">診断中...</div>
            <div style="font-size:0.85rem; color:#8a8a8a;">あなたにぴったりのカードを探しています</div>
        </div>
    `;
    document.getElementById("resultsSection").style.display = "block";
    document.getElementById("resultsContainer").innerHTML = loadingHtml;

    try {
        const resp = await fetch("/recommend", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(answers),
        });
        const data = await resp.json();
        renderResults(data.recommendations);
    } catch (e) {
        document.getElementById("resultsContainer").innerHTML = `
            <div style="text-align:center; padding:40px; color:#8a8a8a; font-size:0.9rem;">
                エラーが発生しました。もう一度お試しください。
            </div>
        `;
    }
}

function renderResults(recommendations) {
    const ranks = ["gold", "silver", "bronze", "other", "other"];
    const rankNums = ["1", "2", "3", "4", "5"];

    const html = recommendations.map((rec, i) => {
        const card = rec.card;
        const imgHtml = card.image_url
            ? `<img src="${card.image_url}" alt="${card.name}" onerror="this.style.display='none'">`
            : `<div style="font-size:2rem; color:#3a3a3a;">💳</div>`;
        const tagsHtml = (card.tags || []).slice(0, 4).map(t => `<span class="tag">${t}</span>`).join("");
        const affiliateUrl = card.affiliate_url || "#";
        return `
            <div class="result-card">
                <div class="result-rank ${ranks[i]}">${rankNums[i]}</div>
                <div class="result-body">
                    <div style="width:64px; height:40px; display:flex; align-items:center; justify-content:center; flex-shrink:0;">${imgHtml}</div>
                    <div class="result-info">
                        <h3>${card.name}</h3>
                        <div class="result-fee">${card.annual_fee_text}</div>
                        <div class="result-rate">還元率 ${card.point_rate}</div>
                        <div class="result-tags">${tagsHtml}</div>
                        <div class="result-score">MATCH SCORE: ${rec.score}</div>
                    </div>
                </div>
                <div class="result-cta">
                    <a href="${affiliateUrl}" target="_blank" rel="noopener nofollow">詳細を見る</a>
                </div>
            </div>
        `;
    }).join("");

    const retryBtn = `
        <div style="text-align:center; margin-top:48px;">
            <button class="btn-secondary" onclick="restartQuiz()">もう一度診断する</button>
            <a href="/cards" class="btn-secondary" style="margin-left:12px;">すべてのカードを見る</a>
        </div>
    `;

    document.getElementById("resultsContainer").innerHTML = html + retryBtn;
    document.getElementById("resultsSection").scrollIntoView({ behavior: "smooth" });
}

function restartQuiz() {
    document.getElementById("resultsSection").style.display = "none";
    startQuiz();
}
