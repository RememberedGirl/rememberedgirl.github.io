import React, { useState, useEffect, useRef } from 'react';
import './App.css';

const GRID_SIZE = 20; // Размер сетки
const TILE_SIZE = 20; // Размер одной клетки
const GAME_SPEED = 150; // Скорость игры (в миллисекундах)

function App() {
    const [snake, setSnake] = useState([{ x: 10, y: 10 }]); // Начальное положение змейки
    const [food, setFood] = useState({ x: 5, y: 5 }); // Начальное положение еды
    const [direction, setDirection] = useState({ x: 0, y: 0 }); // Направление движения
    const [gameOver, setGameOver] = useState(false); // Состояние игры
    const gameAreaRef = useRef(null);

    // Генерация новой еды
    const generateFood = () => {
        let newFood;
        do {
            newFood = {
                x: Math.floor(Math.random() * GRID_SIZE),
                y: Math.floor(Math.random() * GRID_SIZE),
            };
        } while (snake.some((segment) => segment.x === newFood.x && segment.y === newFood.y)); // Проверка, чтобы еда не появилась на змейке
        setFood(newFood);
    };

    // Движение змейки
    const moveSnake = () => {
        if (gameOver || (direction.x === 0 && direction.y === 0)) return; // Не двигаться, если игра окончена или направление не задано

        const newSnake = [...snake];
        const head = { ...newSnake[0] };

        // Новое положение головы
        head.x += direction.x;
        head.y += direction.y;

        // Проверка на столкновение с границами
        if (head.x < 0 || head.x >= GRID_SIZE || head.y < 0 || head.y >= GRID_SIZE) {
            setGameOver(true);
            return;
        }

        // Проверка на столкновение с собой
        if (newSnake.some((segment) => segment.x === head.x && segment.y === head.y)) {
            setGameOver(true);
            return;
        }

        newSnake.unshift(head);

        // Проверка на съедание еды
        if (head.x === food.x && head.y === food.y) {
            generateFood();
        } else {
            newSnake.pop();
        }

        setSnake(newSnake);
    };

    // Обработка нажатий клавиш
    useEffect(() => {
        const handleKeyDown = (e) => {
            switch (e.key) {
                case 'ArrowUp':
                    if (direction.y === 0) setDirection({ x: 0, y: -1 });
                    break;
                case 'ArrowDown':
                    if (direction.y === 0) setDirection({ x: 0, y: 1 });
                    break;
                case 'ArrowLeft':
                    if (direction.x === 0) setDirection({ x: -1, y: 0 });
                    break;
                case 'ArrowRight':
                    if (direction.x === 0) setDirection({ x: 1, y: 0 });
                    break;
                default:
                    break;
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [direction]);

    // Запуск игры
    useEffect(() => {
        const gameInterval = setInterval(moveSnake, GAME_SPEED);
        return () => clearInterval(gameInterval);
    }, [snake, gameOver, direction]);

    // Сброс игры
    const resetGame = () => {
        setSnake([{ x: 10, y: 10 }]);
        setFood({ x: 5, y: 5 });
        setDirection({ x: 0, y: 0 });
        setGameOver(false);
    };

    return (
        <div className="game-container">
            <h1>Змейка</h1>
            <div
                ref={gameAreaRef}
                className="game-area"
                style={{
                    width: `${GRID_SIZE * TILE_SIZE}px`,
                    height: `${GRID_SIZE * TILE_SIZE}px`,
                }}
            >
                {snake.map((segment, index) => (
                    <div
                        key={index}
                        className="snake-segment"
                        style={{
                            left: `${segment.x * TILE_SIZE}px`,
                            top: `${segment.y * TILE_SIZE}px`,
                            width: `${TILE_SIZE}px`,
                            height: `${TILE_SIZE}px`,
                        }}
                    />
                ))}
                <div
                    className="food"
                    style={{
                        left: `${food.x * TILE_SIZE}px`,
                        top: `${food.y * TILE_SIZE}px`,
                        width: `${TILE_SIZE}px`,
                        height: `${TILE_SIZE}px`,
                    }}
                />
            </div>
            {gameOver && (
                <div className="game-over">
                    <p>Игра окончена!</p>
                    <button onClick={resetGame}>Начать заново</button>
                </div>
            )}
        </div>
    );
}

export default App;