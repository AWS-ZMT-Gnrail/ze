// الجلب للعناصر من HTML
const showCodeButton = document.getElementById('showCodeButton');
const codeContainer = document.getElementById('code-container');
const timeLeftElement = document.getElementById('time-left');
const progressBar = document.getElementById('progress-bar');

// عند الضغط على الزر، يتم عرض الكود والزمن المتبقي
showCodeButton.addEventListener('click', () => {
    codeContainer.classList.remove('hidden');
    startCountdown();
});

// دالة العد التنازلي
function startCountdown() {
    let timeLeft = 60; // عدد الثواني المتبقية (يمكنك تغييره حسب الحاجة)
    let interval = setInterval(() => {
        timeLeft--;
        timeLeftElement.textContent = timeLeft; // تحديث الوقت المتبقي
        progressBar.value = 60 - timeLeft; // تحديث شريط التقدم
        if (timeLeft <= 0) {
            clearInterval(interval); // إيقاف العد التنازلي
            alert("انتهى الوقت!");
        }
    }, 1000); // التحديث كل ثانية
}
