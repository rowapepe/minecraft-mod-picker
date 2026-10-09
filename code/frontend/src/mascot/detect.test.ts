import { describe, expect, it } from 'vitest';
import { detectCostume } from './detect';

const id = (t: string) => detectCostume(t).id;

describe('detectCostume (RULE-MASCOT-02)', () => {
  it('примеры запросов из документации', () => {
    expect(id('Хочу автоматизировать ферму и не получить лагов')).toBe('farmer');
    expect(id('Нужен мод, чтобы удобно хранить много предметов')).toBe('builder');
    expect(id('Хочу улучшить производительность на слабом компьютере')).toBe('racer');
    expect(id('Ищу мод с новой генерацией мира и приключениями')).toBe('miner');
  });

  it('по одному костюму на тему', () => {
    expect(id('хочу красивые шейдеры')).toBe('shades');
    expect(id('нужна магия и заклинания')).toBe('wizard');
    expect(id('хочу сражаться с боссами и пользоваться мечом')).toBe('knight');
    expect(id('копать руду в пещерах')).toBe('miner');
    expect(id('хочу строить красивые дома и декор')).toBe('builder');
  });

  it('без совпадений — без костюма', () => {
    expect(id('')).toBe('base');
    expect(id('привет')).toBe('base');
  });

  it('совпадение по началу слова, а не по подстроке', () => {
    expect(id('трудно найти')).toBe('base');
    expect(id('романтика')).toBe('base');
  });

  it('знак $ требует целого слова', () => {
    expect(id('мечта')).toBe('base');
    expect(id('меч')).toBe('knight');
    expect(id('домашний')).toBe('base');
    expect(id('мой дом')).toBe('builder');
  });

  it('регистр и буква ё не важны', () => {
    expect(id('ФЕРМА')).toBe('farmer');
    expect(id('боёв')).toBe('knight');
  });

  it('больше совпадений побеждает, при равенстве — верхний костюм', () => {
    expect(id('оптимизация и производительность на ферме')).toBe('racer');
    expect(id('ферма и лаги')).toBe('farmer');
  });
});
