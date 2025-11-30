(function ($) {
  'use strict';
  $.fn.andSelf = function () {
    return this.addBack.apply(this, arguments);
  }

  $(function () {

    // === Cercle du solde actuel ===
    if ($("#currentBalanceCircle").length) {
      var bar = new ProgressBar.Circle(currentBalanceCircle, {
        color: '#000',
        strokeWidth: 12,
        trailWidth: 12,
        trailColor: '#0d0d0d',
        easing: 'easeInOut',
        duration: 1400,
        text: { autoStyleContainer: false },
        from: { color: '#d53f3a', width: 12 },
        to: { color: '#d53f3a', width: 12 },
        step: function (state, circle) {
          circle.path.setAttribute('stroke', state.color);
          circle.path.setAttribute('stroke-width', state.width);
          var value = Math.round(circle.value() * 100);
          circle.setText('');
        }
      });
      bar.text.style.fontSize = '1.5rem';
      bar.animate(0.4);
    }


    // === GRAPHE : Historique des transactions ===
    if ($("#transaction-history").length) {

      const chartLabels = window.transactionData?.labels || [];
      const chartData = window.transactionData?.data || [];

      console.log('Labels:', chartLabels);
      console.log('Data:', chartData);

      var areaData = {
        labels: chartLabels,
        datasets: [{
          data: chartData,
          backgroundColor: [
            "#111111",
            "#00d25b",
            "#ffab00",
            "#0090e7"
          ]
        }]
      };

      var areaOptions = {
        responsive: true,
        maintainAspectRatio: true,
        cutoutPercentage: 70,
        elements: { arc: { borderWidth: 0 } },
        legend: { display: false },
        tooltips: { enabled: true }
      };

      var transactionhistoryChartCanvas = $("#transaction-history").get(0).getContext("2d");

      var transactionhistoryChart = new Chart(transactionhistoryChartCanvas, {
        type: 'doughnut',
        data: areaData,
        options: areaOptions,
        plugins: [{
          beforeDraw: function (chart) {
            var width = chart.chart.width,
              height = chart.chart.height,
              ctx = chart.chart.ctx;

            ctx.restore();

            // 🔹 Total au centre du donut
            var total = chartData.reduce((a, b) => a + b, 0).toFixed(2);
            ctx.font = "1rem sans-serif";
            ctx.fillStyle = "#ffffff";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillText(`$${total}`, width / 2, height / 2.4);

            // 🔹 Légende "Total"
            ctx.font = "0.75rem sans-serif";
            ctx.fillStyle = "#6c7293";
            ctx.fillText("Total", width / 2, height / 1.7);

            ctx.save();
          }
        }]
      });
    }

    // === Carrousel basique ===
    if ($('#owl-carousel-basic').length) {
      $('#owl-carousel-basic').owlCarousel({
        loop: true,
        margin: 10,
        dots: false,
        nav: true,
        autoplay: true,
        autoplayTimeout: 4500,
        navText: ["<i class='mdi mdi-chevron-left'></i>", "<i class='mdi mdi-chevron-right'></i>"],
        responsive: { 0: { items: 1 }, 600: { items: 1 }, 1000: { items: 1 } }
      });
    }

    // === Carrousel RTL ===
    var isrtl = $("body").hasClass("rtl");
    if ($('#owl-carousel-rtl').length) {
      $('#owl-carousel-rtl').owlCarousel({
        loop: true,
        margin: 10,
        dots: false,
        nav: true,
        rtl: isrtl,
        autoplay: true,
        autoplayTimeout: 4500,
        navText: ["<i class='mdi mdi-chevron-right'></i>", "<i class='mdi mdi-chevron-left'></i>"],
        responsive: { 0: { items: 1 }, 600: { items: 1 }, 1000: { items: 1 } }
      });
    }

  });
})(jQuery);
