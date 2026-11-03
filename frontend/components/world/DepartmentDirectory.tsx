/* 기관 네 곳의 편제와 역할을 표시한다. */
import { DEPARTMENTS } from "../../lib/world";
export function DepartmentDirectory() {
  /* 기관 네 곳의 편제와 역할을 표시한다. */

  return (
    <section className="department-directory" aria-label="기관 구성">
      <div className="directory-title">
        <span>기관 편제</span>
        <small>ORGANIZATION / 04</small>
      </div>
      <div className="department-grid">
        {DEPARTMENTS.map((department) => {
          /* 각 항목의 화면 요소를 반환한다. */ return (
            <article
              className={`department ${department.tone}`}
              key={department.id}
            >
              <span className="department-number">{department.id}</span>
              <div>
                <h3>{department.name}</h3>
                <small>{department.role}</small>
                <p>{department.description}</p>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
