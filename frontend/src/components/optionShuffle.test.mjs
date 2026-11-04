import { test } from 'node:test'
import assert from 'node:assert/strict'
import { shuffleOptions } from './optionShuffle.mjs'

test('shuffles without changing the number or ID associated with each choice', () => {
  const original = [{ id: 10, number: 1, text: 'A' }, { id: 11, number: 2, text: 'B' }, { id: 12, number: 3, text: 'C' }]
  const shuffled = shuffleOptions(original, () => 0)
  assert.deepEqual(shuffled.map(option => [option.id, option.number, option.text]), [[11, 2, 'B'], [12, 3, 'C'], [10, 1, 'A']])
  assert.deepEqual(original.map(option => option.id), [10, 11, 12])
})

test('legacy choices keep their original numbers when reordered', () => {
  const shuffled = shuffleOptions([{ text: 'A' }, { text: 'B' }, { text: 'C' }], () => 0)
  assert.deepEqual(shuffled.map(option => [option.text, option.number]), [['B', 2], ['C', 3], ['A', 1]])
  assert.deepEqual(shuffleOptions(undefined), [])
})
