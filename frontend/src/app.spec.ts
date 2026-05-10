import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';
import { createMemoryHistory, createRouter } from 'vue-router';
import App from './App.vue';
import { routes } from './router';

describe('App shell', () => {
  it('mounts layout with navigation and outlet', async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes,
    });
    await router.push('/');
    await router.isReady();

    const wrapper = mount(App, {
      global: {
        plugins: [router],
      },
    });

    expect(wrapper.text()).toContain('SRF News Lernen');
    expect(wrapper.text()).toContain('Mobile-first App-Shell');
    expect(wrapper.find('main').exists()).toBe(true);
    expect(wrapper.text()).toContain('App-Shell bereit');
  });
});
