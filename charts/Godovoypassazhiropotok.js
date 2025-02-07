// script.js

document.addEventListener('DOMContentLoaded', function () {
    // Загрузка данных
    fetch('charts/Godovoypassazhiropotok.json')
        .then(response => response.json())
        .then(data => {
            // Группировка данных по годам и типам транспорта
            const years = [...new Set(data.map(item => item.Year))];
            const transportTypes = [...new Set(data.map(item => item.TransportType))];

            // Сортировка категорий по убыванию (по суммарному пассажиропотоку)
            const sortedTransportTypes = transportTypes.sort((a, b) => {
                const sumA = data
                    .filter(item => item.TransportType === a)
                    .reduce((sum, item) => sum + Number(item.PassengerTraffic), 0);
                const sumB = data
                    .filter(item => item.TransportType === b)
                    .reduce((sum, item) => sum + Number(item.PassengerTraffic), 0);
                return sumB - sumA; // Сортировка по убыванию
            });

            // Подготовка данных для графика
            const series = sortedTransportTypes.map(type => {
                return {
                    name: type,
                    data: years.map(year => {
                        const item = data.find(d => d.Year === year && d.TransportType === type);
                        return item ? Number(item.PassengerTraffic) : 0;
                    })
                };
            });

            // Создание графика
            Highcharts.chart('container', {
                chart: {
                    type: 'column'
                },
                title: {
                    text: 'Годовой пассажиропоток по видам транспорта'
                },
                xAxis: {
                    categories: years,
                    title: {
                        text: 'Год'
                    }
                },
                yAxis: {
                    min: 0,
                    title: {
                        text: 'Пассажиропоток'
                    }
                },
                plotOptions: {
                    column: {
                        stacking: 'normal'
                    }
                },
                series: series
            });
        });
});