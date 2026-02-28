// src/pages/Landing.tsx
// InfoLens AI — Public landing page (foundation for future marketing site)
import { useEffect, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import "./Landing.css";

const FEATURES = [
  {
    icon: "🧠",
    title: "Phân tích AI thông minh",
    desc: "Sử dụng mô hình ngôn ngữ lớn để phân tích sâu nội dung, trích xuất ý chính và đánh giá cảm xúc văn bản.",
  },
  {
    icon: "💬",
    title: "Chat với tài liệu",
    desc: "Đặt câu hỏi trực tiếp về nội dung tài liệu và nhận câu trả lời chính xác, có trích dẫn nguồn.",
  },
  {
    icon: "✍️",
    title: "Viết lại & cải thiện",
    desc: "Tự động viết lại văn bản theo phong cách mong muốn: chuyên nghiệp, học thuật, sáng tạo hay đơn giản hơn.",
  },
  {
    icon: "📊",
    title: "Thống kê chi tiết",
    desc: "Xem thống kê từ vựng, độ phức tạp, cấu trúc câu và nhiều chỉ số ngôn ngữ học khác.",
  },
  {
    icon: "📚",
    title: "Lịch sử & quản lý",
    desc: "Lưu trữ và quản lý toàn bộ tài liệu đã phân tích, dễ dàng tìm kiếm và truy cập lại.",
  },
  {
    icon: "🔒",
    title: "Bảo mật dữ liệu",
    desc: "Dữ liệu của bạn được mã hóa và bảo vệ. Chúng tôi không chia sẻ thông tin với bên thứ ba.",
  },
];

const STEPS = [
  {
    title: "Tạo tài khoản miễn phí",
    desc: "Đăng ký chỉ mất 30 giây. Không cần thẻ tín dụng.",
  },
  {
    title: "Upload hoặc dán văn bản",
    desc: "Hỗ trợ file PDF, Word, TXT hoặc dán trực tiếp URL trang web.",
  },
  {
    title: "Nhận phân tích tức thì",
    desc: "AI xử lý và trả về kết quả phân tích toàn diện trong vài giây.",
  },
  {
    title: "Khám phá & tương tác",
    desc: "Chat, viết lại, xuất báo cáo và chia sẻ kết quả với đồng nghiệp.",
  },
];

export default function Landing() {
  const navigate = useNavigate();
  const navRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const handleScroll = () => {
      if (navRef.current) {
        navRef.current.classList.toggle("scrolled", window.scrollY > 20);
      }
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <div className="landing-page">
      {/* ── Navbar ── */}
      <nav className="landing-nav" ref={navRef}>
        <Link to="/" className="landing-nav-logo">
          <div className="landing-nav-logo-icon">✨</div>
          <span className="landing-nav-logo-text">InfoLens AI</span>
        </Link>

        <ul className="landing-nav-links">
          <li><a href="#features">Tính năng</a></li>
          <li><a href="#how-it-works">Cách dùng</a></li>
        </ul>

        <div className="landing-nav-cta">
          <button
            className="btn btn-ghost btn-sm"
            onClick={() => navigate("/login")}
          >
            Đăng nhập
          </button>
          <button
            className="btn btn-brand btn-sm"
            onClick={() => navigate("/login")}
          >
            Dùng miễn phí →
          </button>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className="hero">
        <div className="hero-content">
          <div className="hero-badge">
            <span className="hero-badge-dot" />
            Powered by Advanced AI Models
          </div>

          <h1 className="hero-title">
            Phân tích văn bản{" "}
            <span className="hero-title-gradient">thông minh hơn</span>
            {" "}với AI
          </h1>

          <p className="hero-subtitle">
            InfoLens AI giúp bạn hiểu sâu hơn về bất kỳ văn bản nào — từ phân tích
            cảm xúc, trích xuất ý chính đến chat trực tiếp với tài liệu.
          </p>

          <div className="hero-actions">
            <button
              className="hero-btn-primary"
              onClick={() => navigate("/login")}
            >
              🚀 Bắt đầu miễn phí
            </button>
            <a href="#features" className="hero-btn-secondary">
              Xem tính năng ↓
            </a>
          </div>

          <div className="hero-stats">
            {[
              { value: "10+", label: "Loại phân tích" },
              { value: "< 3s", label: "Thời gian xử lý" },
              { value: "100%", label: "Bảo mật dữ liệu" },
            ].map((s) => (
              <div key={s.label} style={{ textAlign: "center" }}>
                <div className="hero-stat-value">{s.value}</div>
                <div className="hero-stat-label">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features ── */}
      <section className="features-section" id="features">
        <div className="features-header">
          <span className="features-eyebrow">Tính năng</span>
          <h2 className="features-title">Mọi thứ bạn cần để hiểu văn bản</h2>
          <p className="features-desc">
            Bộ công cụ AI toàn diện giúp bạn khai thác tối đa giá trị từ mọi tài liệu.
          </p>
        </div>

        <div className="features-grid">
          {FEATURES.map((f) => (
            <div className="feature-card" key={f.title}>
              <div className="feature-icon">{f.icon}</div>
              <h3 className="feature-title">{f.title}</h3>
              <p className="feature-desc">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── How It Works ── */}
      <section className="how-section" id="how-it-works">
        <div className="features-header">
          <span className="features-eyebrow">Cách sử dụng</span>
          <h2 className="features-title">Bắt đầu trong 4 bước đơn giản</h2>
          <p className="features-desc">
            Không cần cài đặt, không cần kỹ thuật. Chỉ cần trình duyệt là đủ.
          </p>
        </div>

        <ol className="steps-list">
          {STEPS.map((step, i) => (
            <li className="step-item" key={step.title}>
              <div className="step-number">{i + 1}</div>
              <div>
                <h3 className="step-content-title">{step.title}</h3>
                <p className="step-content-desc">{step.desc}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      {/* ── CTA ── */}
      <section className="cta-section">
        <div className="cta-content">
          <h2 className="cta-title">Sẵn sàng phân tích văn bản thông minh hơn?</h2>
          <p className="cta-desc">
            Tham gia ngay hôm nay và trải nghiệm sức mạnh của AI trong việc hiểu văn bản.
          </p>
          <button
            className="hero-btn-primary"
            onClick={() => navigate("/login")}
          >
            🚀 Tạo tài khoản miễn phí
          </button>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="landing-footer">
        <div className="landing-footer-grid">
          <div>
            <h3 className="footer-brand-name">InfoLens AI</h3>
            <p className="footer-brand-desc">
              Nền tảng phân tích văn bản thông minh sử dụng trí tuệ nhân tạo,
              giúp bạn hiểu sâu hơn về mọi tài liệu.
            </p>
          </div>

          <div>
            <h4 className="footer-col-title">Sản phẩm</h4>
            <ul className="footer-links">
              <li><a href="#features">Tính năng</a></li>
              <li><a href="#how-it-works">Cách dùng</a></li>
            </ul>
          </div>

          <div>
            <h4 className="footer-col-title">Tài khoản</h4>
            <ul className="footer-links">
              <li><Link to="/login">Đăng nhập</Link></li>
              <li><Link to="/login">Đăng ký</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="footer-col-title">Hỗ trợ</h4>
            <ul className="footer-links">
              <li><a href="#">Liên hệ</a></li>
              <li><a href="#">Chính sách bảo mật</a></li>
            </ul>
          </div>
        </div>

        <div className="footer-bottom">
          <span>© {new Date().getFullYear()} InfoLens AI. All rights reserved.</span>
          <span>Made with ❤️ in Vietnam</span>
        </div>
      </footer>
    </div>
  );
}

