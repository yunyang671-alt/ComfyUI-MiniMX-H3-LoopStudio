import assert from 'node:assert/strict';
import { isModelChoice, resolveWidgetChoices, refreshWidgetChoices } from '../js/widget_choices.js';

// Model identity must survive an empty/dynamic catalog and catalog refresh.
const widget = { value: 'tested-ref2v8.safetensors', options: { values: ['other.safetensors'] } };
const select = { dataset: {}, ownerDocument: { createElement: () => ({}) },
  replaceChildren(...children) { this.children = children; } };
assert.equal(refreshWidgetChoices(select, widget), 1);
assert.equal(select.value, widget.value);
assert.deepEqual(select.children.map(x => x.value), [widget.value, 'other.safetensors']);
let catalog = ['tested-ref2v8.safetensors', 'another.safetensors'];
widget.options.values = received => { assert.equal(received, widget); return catalog; };
assert.equal(refreshWidgetChoices(select, widget), 2);
catalog = ['new-model.safetensors'];
assert.equal(refreshWidgetChoices(select, widget), 1);
assert.equal(select.value, widget.value);
assert.equal(select.children[1].value, 'new-model.safetensors');
widget.options.values = () => { throw Error('catalog unavailable'); };
assert.equal(refreshWidgetChoices(select, widget), 0);
assert.equal(select.value, 'tested-ref2v8.safetensors');
assert.equal(widget.value, 'tested-ref2v8.safetensors');
assert.deepEqual(resolveWidgetChoices({ options: { values: { 'a.safetensors': 1, 'b.safetensors': 2 } } }), ['a.safetensors', 'b.safetensors']);
assert.deepEqual(resolveWidgetChoices({ options: { items: ['a', 'a', 7, null, {}] } }), ['a', 7]);
assert.deepEqual(resolveWidgetChoices({ options: { values: () => Promise.resolve(['unavailable-synchronous-option']) } }), []);
assert.deepEqual(resolveWidgetChoices(null), []);
for (const name of ['模型', '文本编码器', '视频VAE', '音频VAE', '二采放大模型', 'LoRA1', 'LoRA6']) assert.ok(isModelChoice(name));
for (const name of ['LoRA1强度', '提示词', '时长秒']) assert.equal(isModelChoice(name), false);
console.log('PASS: dynamic/static/object model choices, provider failures, refreshed catalogs, and exact saved model preservation.');
