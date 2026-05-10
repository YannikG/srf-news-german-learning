import { createRouter, createWebHistory } from 'vue-router';
import HomeView from '@/views/HomeView.vue';
import StubView from '@/views/StubView.vue';

export const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
    meta: { title: 'Start' },
  },
  {
    path: '/stub',
    name: 'stub',
    component: StubView,
    meta: { title: 'Platzhalter' },
  },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
});
